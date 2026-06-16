import { chromium, Browser, Page } from 'playwright';
import * as cheerio from 'cheerio';
import { logger } from '../utils/logger';
import { randomDelay, delayBetweenDomains, getRandomUserAgent } from '../utils/delays';
import { NotFoundError, RateLimitError, ScraperError } from '../utils/errors';

export interface DiscoveredSource {
  url: string;
  type: 'search_result' | 'linkedin' | 'directory' | 'crunchbase' | 'company_website';
  companyName?: string;
  snippet?: string;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

// Search queries to generate for source discovery
function generateSearchQueries(industry: string, country: string): string[] {
  return [
    `${industry} companies in ${country}`,
    `top ${industry} startups ${country}`,
    `${industry} directory ${country}`,
    `list of ${industry} companies ${country}`,
    `best ${industry} firms ${country}`,
    `${industry} tech companies ${country}`,
    `${industry} startups to watch ${country}`,
    `${industry} companies list ${country}`,
    `leading ${industry} providers ${country}`,
    `${industry} industry leaders ${country}`,
  ];
}

// Initialize browser for source discovery
let browser: Browser | null = null;

async function getBrowser(): Promise<Browser> {
  if (!browser) {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
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

async function searchGoogle(
  query: string,
  page: Page
): Promise<SearchResult[]> {
  const results: SearchResult[] = [];
  const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}&num=10`;
  
  try {
    await page.goto(searchUrl, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });
    
    // Wait a bit for dynamic content
    await randomDelay(2000, 4000);
    
    const content = await page.content();
    const $ = cheerio.load(content);
    
    // Parse search results
    $('div.g').each((_, element) => {
      const titleElement = $(element).find('h3');
      const linkElement = $(element).find('a');
      const snippetElement = $(element).find('div[data-sncf]');
      
      const title = titleElement.text().trim();
      const url = linkElement.attr('href') || '';
      const snippet = snippetElement.text().trim() || $(element).find('span').first().text().trim();
      
      if (url && title) {
        results.push({ title, url, snippet });
      }
    });
    
    logger.debug('Search results parsed', {
      query: query.substring(0, 50),
      resultCount: results.length,
    });
  } catch (error) {
    logger.warn('Failed to search Google', {
      query: query.substring(0, 50),
      error: (error as Error).message,
    });
  }
  
  return results;
}

function extractUrlsFromResults(results: SearchResult[]): string[] {
  const urls: string[] = [];
  
  for (const result of results) {
    // Extract domain from URL
    try {
      const urlObj = new URL(result.url.startsWith('http') ? result.url : `https://${result.url}`);
      urls.push(urlObj.href);
    } catch {
      // Skip invalid URLs
    }
  }
  
  return [...new Set(urls)];
}

function categorizeUrl(url: string, title: string): DiscoveredSource['type'] {
  const lowerUrl = url.toLowerCase();
  const lowerTitle = title.toLowerCase();
  
  if (lowerUrl.includes('linkedin.com/company')) {
    return 'linkedin';
  }
  if (lowerUrl.includes('crunchbase.com')) {
    return 'crunchbase';
  }
  if (lowerUrl.includes('directory') || lowerUrl.includes('list') || lowerUrl.includes('registry')) {
    return 'directory';
  }
  if (lowerTitle.includes('company') || lowerTitle.includes('startup')) {
    return 'company_website';
  }
  
  return 'search_result';
}

function extractCompanyNameFromUrl(url: string, title: string): string | undefined {
  // Try to extract from title
  const titleMatch = title.match(/^([^-|]+)/);
  if (titleMatch) {
    return titleMatch[1].trim();
  }
  
  // Try to extract from URL domain
  try {
    const urlObj = new URL(url);
    const domain = urlObj.hostname.replace(/^www\./, '');
    const name = domain.split('.')[0];
    if (name && name.length > 2 && !['google', 'bing', 'linkedin', 'crunchbase'].includes(name)) {
      return name.charAt(0).toUpperCase() + name.slice(1);
    }
  } catch {
    // Ignore
  }
  
  return undefined;
}

export async function discoverSources(
  industry: string,
  country: string,
  maxResultsPerQuery = 10
): Promise<DiscoveredSource[]> {
  const browserInstance = await getBrowser();
  const page = await browserInstance.newPage();
  
  // Set user agent
  await page.setExtraHTTPHeaders({
    'User-Agent': getRandomUserAgent(),
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  });
  
  const queries = generateSearchQueries(industry, country);
  const allSources: DiscoveredSource[] = [];
  const seenUrls = new Set<string>();
  
  logger.info('Starting source discovery', {
    industry,
    country,
    queryCount: queries.length,
  });
  
  for (const query of queries) {
    try {
      logger.debug('Searching', { query: query.substring(0, 60) });
      
      const results = await searchGoogle(query, page);
      const urls = extractUrlsFromResults(results);
      
      for (const result of results) {
        const url = result.url;
        if (seenUrls.has(url)) continue;
        seenUrls.add(url);
        
        const source: DiscoveredSource = {
          url,
          type: categorizeUrl(url, result.title),
          companyName: extractCompanyNameFromUrl(url, result.title),
          snippet: result.snippet,
        };
        
        allSources.push(source);
      }
      
      // Rate limiting between queries
      await delayBetweenDomains();
      
    } catch (error) {
      logger.error('Query failed', {
        query: query.substring(0, 60),
        error: (error as Error).message,
      });
    }
  }
  
  await page.close();
  
  // Deduplicate by URL
  const uniqueSources = allSources.filter((source, index, self) =>
    index === self.findIndex(s => s.url === source.url)
  );
  
  logger.info('Source discovery complete', {
    totalSources: uniqueSources.length,
    byType: {
      linkedin: uniqueSources.filter(s => s.type === 'linkedin').length,
      directory: uniqueSources.filter(s => s.type === 'directory').length,
      crunchbase: uniqueSources.filter(s => s.type === 'crunchbase').length,
      company_website: uniqueSources.filter(s => s.type === 'company_website').length,
      search_result: uniqueSources.filter(s => s.type === 'search_result').length,
    },
  });
  
  return uniqueSources;
}

export async function discoverFromDirectory(
  directoryUrl: string,
  page: Page
): Promise<DiscoveredSource[]> {
  const sources: DiscoveredSource[] = [];
  
  try {
    await page.goto(directoryUrl, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });
    
    await randomDelay(2000, 4000);
    
    const content = await page.content();
    const $ = cheerio.load(content);
    
    // Extract company links from directory page
    $('a[href*="company"]').each((_, element) => {
      const href = $(element).attr('href');
      const text = $(element).text().trim();
      
      if (href && text && text.length > 2) {
        sources.push({
          url: href.startsWith('http') ? href : new URL(href, directoryUrl).href,
          type: 'directory',
          companyName: text,
        });
      }
    });
    
    logger.debug('Directory parsed', {
      url: directoryUrl,
      companyCount: sources.length,
    });
  } catch (error) {
    logger.warn('Failed to parse directory', {
      url: directoryUrl,
      error: (error as Error).message,
    });
  }
  
  return sources;
}

export async function discoverFromLinkedIn(
  linkedinUrl: string,
  page: Page
): Promise<DiscoveredSource[]> {
  const sources: DiscoveredSource[] = [];
  
  try {
    await page.goto(linkedinUrl, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });
    
    await randomDelay(3000, 5000);
    
    const content = await page.content();
    const $ = cheerio.load(content);
    
    // Extract company profile links
    $('a[href*="/company/"]').each((_, element) => {
      const href = $(element).attr('href');
      const text = $(element).find('.org-top-card-summary__title').text().trim() ||
                   $(element).text().trim();
      
      if (href && text) {
        const fullUrl = href.startsWith('http')
          ? href
          : `https://www.linkedin.com${href}`;
        
        sources.push({
          url: fullUrl,
          type: 'linkedin',
          companyName: text.substring(0, 100),
        });
      }
    });
    
    logger.debug('LinkedIn page parsed', {
      url: linkedinUrl,
      companyCount: sources.length,
    });
  } catch (error) {
    logger.warn('Failed to parse LinkedIn', {
      url: linkedinUrl,
      error: (error as Error).message,
    });
  }
  
  return sources;
}