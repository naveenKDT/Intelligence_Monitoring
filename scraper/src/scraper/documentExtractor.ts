import { chromium, Browser, Page } from 'playwright';
import * as cheerio from 'cheerio';
import { logger } from '../utils/logger';
import { randomDelay, delayForDomain, getRandomUserAgent } from '../utils/delays';
import { extractDomainFromUrl } from '../deduplication/normalizer';

export type DocumentType = 'blog' | 'press_release' | 'pdf' | 'news' | 'social' | 'article' | 'documentation';

export interface ExtractedDocument {
  title: string;
  url: string;
  content: string;
  doc_type: DocumentType;
  published_date?: Date;
  source_url: string;
}

const MAX_DOCUMENTS_PER_COMPANY = 50;

let browser: Browser | null = null;

async function getBrowser(): Promise<Browser> {
  if (!browser) {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    });
  }
  return browser;
}

export async function closeBrowser(): Promise<void> {
  if (browser) {
    await browser.close();
    browser = null;
  }
}

function detectDocumentType(url: string, title: string): DocumentType {
  const lowerUrl = url.toLowerCase();
  const lowerTitle = title.toLowerCase();
  
  if (lowerUrl.endsWith('.pdf') || lowerUrl.includes('.pdf?')) {
    return 'pdf';
  }
  if (lowerUrl.includes('/blog') || lowerUrl.includes('/posts') || lowerTitle.includes('blog')) {
    return 'blog';
  }
  if (lowerUrl.includes('/news') || lowerUrl.includes('/press') || lowerUrl.includes('/newsroom') || lowerTitle.includes('press release')) {
    return 'press_release';
  }
  if (lowerUrl.includes('/article') || lowerTitle.includes('article')) {
    return 'article';
  }
  if (lowerUrl.includes('linkedin.com') || lowerUrl.includes('twitter.com') || lowerUrl.includes('x.com')) {
    return 'social';
  }
  if (lowerTitle.includes('news')) {
    return 'news';
  }
  if (lowerUrl.includes('/docs') || lowerUrl.includes('/documentation')) {
    return 'documentation';
  }
  
  return 'article';
}

function extractPublishedDate($: cheerio.Root): Date | undefined {
  // Try meta tags first
  const metaDate = $('meta[property="article:published_time"]').attr('content') ||
                   $('meta[name="publication_date"]').attr('content') ||
                   $('meta[name="date"]').attr('content') ||
                   $('time[datetime]').attr('datetime');
  
  if (metaDate) {
    const parsed = new Date(metaDate);
    if (!isNaN(parsed.getTime())) {
      return parsed;
    }
  }
  
  // Try to find date in content
  const bodyText = $('body').text();
  const datePatterns = [
    /(\w+\s+\d{1,2},?\s+\d{4})/,
    /(\d{1,2}\s+\w+\s+\d{4})/,
    /(\d{4}-\d{2}-\d{2})/,
    /(\d{2}\/\d{2}\/\d{4})/,
  ];
  
  for (const pattern of datePatterns) {
    const match = bodyText.match(pattern);
    if (match) {
      const parsed = new Date(match[1]);
      if (!isNaN(parsed.getTime())) {
        return parsed;
      }
    }
  }
  
  return undefined;
}

function extractTitle($: cheerio.Root, url: string): string {
  // Try various sources for title
  let title = $('meta[property="og:title"]').attr('content');
  if (title) return title;
  
  title = $('meta[name="title"]').attr('content');
  if (title) return title;
  
  title = $('h1').first().text().trim();
  if (title) return title;
  
  title = $('title').text().trim();
  if (title) return title;
  
  // Extract from URL
  try {
    const urlObj = new URL(url);
    const pathParts = urlObj.pathname.split('/').filter(p => p);
    if (pathParts.length > 0) {
      return pathParts[pathParts.length - 1].replace(/-/g, ' ');
    }
  } catch {
    // Ignore
  }
  
  return 'Untitled Document';
}

function extractContent($: cheerio.Root): string {
  // Remove unwanted elements
  $('script, style, nav, header, footer, aside, .sidebar, .navigation, .comments, .advertisement, .ad, .social-share').remove();
  
  // Try to find main content area
  const contentSelectors = [
    'article',
    'main',
    '[class*="content"]',
    '[class*="post"]',
    '[class*="article"]',
    '.entry-content',
    '.post-content',
    '.article-content',
  ];
  
  for (const selector of contentSelectors) {
    const content = $(selector).first();
    if (content.length) {
      const text = content.text().trim();
      if (text.length > 100) {
        return text.replace(/\s+/g, ' ');
      }
    }
  }
  
  // Fall back to body
  return $('body').text().replace(/\s+/g, ' ').trim().substring(0, 10000);
}

async function fetchDocument(url: string, sourceUrl: string): Promise<ExtractedDocument | null> {
  const browserInstance = await getBrowser();
  const page = await browserInstance.newPage();
  
  try {
    await page.goto(url, {
      waitUntil: 'domcontentloaded',
      timeout: 20000,
    });
    
    await randomDelay(1000, 2000);
    
    const content = await page.content();
    const $ = cheerio.load(content);
    
    const title = extractTitle($, url);
    const doc_type = detectDocumentType(url, title);
    const pageContent = extractContent($);
    const published_date = extractPublishedDate($);
    
    return {
      title: title.substring(0, 500),
      url,
      content: pageContent,
      doc_type,
      published_date,
      source_url: sourceUrl,
    };
  } catch (error) {
    logger.debug('Failed to fetch document', {
      url,
      error: (error as Error).message,
    });
    return null;
  } finally {
    await page.close();
  }
}

export async function findDocumentsOnPage(
  pageUrl: string,
  page: Page
): Promise<string[]> {
  const documentUrls: string[] = [];
  
  try {
    const content = await page.content();
    const $ = cheerio.load(content);
    
    // Find links to potential documents
    $('a[href]').each((_, element) => {
      const href = $(element).attr('href');
      if (!href) return;
      
      const fullUrl = href.startsWith('http')
        ? href
        : tryBuildUrl(pageUrl, href);
      
      if (!fullUrl) return;
      
      const lowerUrl = fullUrl.toLowerCase();
      
      // Check for document-like URLs
      if (
        lowerUrl.includes('/blog') ||
        lowerUrl.includes('/news') ||
        lowerUrl.includes('/press') ||
        lowerUrl.includes('/article') ||
        lowerUrl.includes('/posts') ||
        lowerUrl.includes('.pdf')
      ) {
        documentUrls.push(fullUrl);
      }
    });
    
    // Also look for RSS/Atom feeds
    const feedLinks = $('link[type="application/rss+xml"], link[type="application/atom+xml"]').each((_, element) => {
      const href = $(element).attr('href');
      if (href) {
        const fullUrl = href.startsWith('http')
          ? href
          : tryBuildUrl(pageUrl, href);
        if (fullUrl) {
          documentUrls.push(fullUrl);
        }
      }
    });
    
  } catch (error) {
    logger.debug('Failed to find documents on page', {
      url: pageUrl,
      error: (error as Error).message,
    });
  }
  
  // Deduplicate
  return [...new Set(documentUrls)];
}

function tryBuildUrl(baseUrl: string, relativeUrl: string): string | null {
  try {
    return new URL(relativeUrl, baseUrl).href;
  } catch {
    return null;
  }
}

export async function extractDocumentsFromCompany(
  companyUrl: string,
  industry: string
): Promise<ExtractedDocument[]> {
  const domain = extractDomainFromUrl(companyUrl);
  if (!domain) return [];
  
  await delayForDomain(domain);
  
  const browserInstance = await getBrowser();
  const page = await browserInstance.newPage();
  
  await page.setExtraHTTPHeaders({
    'User-Agent': getRandomUserAgent(),
  });
  
  const documents: ExtractedDocument[] = [];
  const documentUrls = new Set<string>();
  
  try {
    // Common document paths to check
    const paths = [
      '/blog',
      '/news',
      '/newsroom',
      '/press',
      '/articles',
      '/posts',
      '/insights',
      '/resources',
      '/whitepapers',
      '/case-studies',
    ];
    
    for (const path of paths) {
      if (documents.length >= MAX_DOCUMENTS_PER_COMPANY) break;
      
      const url = companyUrl.replace(/\/$/, '') + path;
      
      try {
        await page.goto(url, {
          waitUntil: 'domcontentloaded',
          timeout: 15000,
        });
        
        await randomDelay(1500, 3000);
        
        // Find document links on this page
        const urls = await findDocumentsOnPage(url, page);
        for (const docUrl of urls) {
          if (!documentUrls.has(docUrl)) {
            documentUrls.add(docUrl);
          }
        }
      } catch {
        // Page doesn't exist, continue
      }
    }
    
    // Fetch all discovered documents
    logger.debug('Fetching documents', {
      companyUrl,
      documentCount: documentUrls.size,
    });
    
    const urlsArray = Array.from(documentUrls).slice(0, MAX_DOCUMENTS_PER_COMPANY);
    
    for (const docUrl of urlsArray) {
      if (documents.length >= MAX_DOCUMENTS_PER_COMPANY) break;
      
      const doc = await fetchDocument(docUrl, companyUrl);
      if (doc) {
        documents.push(doc);
      }
      
      await randomDelay(1000, 2000);
    }
    
  } finally {
    await page.close();
  }
  
  logger.info('Documents extracted', {
    companyUrl,
    documentCount: documents.length,
  });
  
  return documents;
}

export async function extractPdfDocuments(
  companyUrl: string
): Promise<ExtractedDocument[]> {
  const domain = extractDomainFromUrl(companyUrl);
  if (!domain) return [];
  
  await delayForDomain(domain);
  
  const browserInstance = await getBrowser();
  const page = await browserInstance.newPage();
  
  const documents: ExtractedDocument[] = [];
  
  try {
    await page.goto(companyUrl, {
      waitUntil: 'domcontentloaded',
      timeout: 20000,
    });
    
    await randomDelay(2000, 4000);
    
    const content = await page.content();
    const $ = cheerio.load(content);
    
    // Find PDF links
    $('a[href$=".pdf"], a[href*=".pdf?"]').each((_, element) => {
      const href = $(element).attr('href');
      if (href) {
        const fullUrl = href.startsWith('http')
          ? href
          : tryBuildUrl(companyUrl, href);
        
        if (fullUrl) {
          const title = $(element).text().trim() ||
                       $(element).find('img').attr('alt') ||
                       'PDF Document';
          
          documents.push({
            title: title.substring(0, 500),
            url: fullUrl,
            content: '',
            doc_type: 'pdf',
            source_url: companyUrl,
          });
        }
      }
    });
    
  } catch (error) {
    logger.debug('Failed to extract PDFs', {
      companyUrl,
      error: (error as Error).message,
    });
  } finally {
    await page.close();
  }
  
  return documents.slice(0, 20);
}