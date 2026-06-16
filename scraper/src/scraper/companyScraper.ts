import { chromium, Browser, Page } from 'playwright';
import * as cheerio from 'cheerio';
import { logger } from '../utils/logger';
import { randomDelay, delayForDomain, getRandomUserAgent } from '../utils/delays';
import { hashContent } from '../deduplication/contentHash';
import { extractDomainFromUrl } from '../deduplication/normalizer';
import {
  ScraperError,
  AuthenticationError,
  NotFoundError,
  RateLimitError,
  ParseError,
} from '../utils/errors';

export interface ScrapedCompany {
  company_name: string;
  website_url: string;
  domain: string;
  industry: string;
  country: string;
  region?: string;
  description?: string;
  employee_count?: number;
  founded_year?: number;
  phone?: string;
  primary_email?: string;
  hq_address?: string;
  office_locations?: Record<string, unknown>[];
  linkedin_url?: string;
  twitter_url?: string;
  github_url?: string;
  tech_stack: string[];
  hash_homepage: string;
  sources: string[];
}

export interface RobotRules {
  allowed: boolean;
  crawlDelay?: number;
  disallowPaths: string[];
}

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

async function checkRobotsTxt(domain: string): Promise<RobotRules> {
  const rules: RobotRules = {
    allowed: true,
    disallowPaths: [],
  };
  
  try {
    const robotsUrl = `https://${domain}/robots.txt`;
    const response = await fetch(robotsUrl, {
      headers: {
        'User-Agent': 'CompanyScraper/1.0',
      },
      signal: AbortSignal.timeout(5000),
    });
    
    if (!response.ok) {
      return rules;
    }
    
    const text = await response.text();
    const lines = text.split('\n');
    
    let userAgentMatched = false;
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      if (trimmed.startsWith('User-agent:')) {
        const agent = trimmed.substring(10).trim().toLowerCase();
        userAgentMatched = agent === '*' || agent.includes('scraper') || agent.includes('bot');
      } else if (userAgentMatched) {
        if (trimmed.startsWith('Disallow:')) {
          const path = trimmed.substring(9).trim();
          rules.disallowPaths.push(path);
        } else if (trimmed.startsWith('Allow:')) {
          const path = trimmed.substring(6).trim();
          const index = rules.disallowPaths.indexOf(path);
          if (index >= 0) {
            rules.disallowPaths.splice(index, 1);
          }
        } else if (trimmed.startsWith('Crawl-delay:')) {
          rules.crawlDelay = parseFloat(trimmed.substring(12).trim()) * 1000;
        }
      }
    }
  } catch {
    // robots.txt not found or parse error, assume allowed
  }
  
  return rules;
}

function isLoginPage(url: string, content: string): boolean {
  const lowerUrl = url.toLowerCase();
  const $ = cheerio.load(content);
  const bodyText = $('body').text().toLowerCase();
  
  // Check URL patterns
  if (lowerUrl.includes('/login') || lowerUrl.includes('/signin') || lowerUrl.includes('/auth')) {
    return true;
  }
  
  // Check content for login indicators
  const loginIndicators = [
    'sign in',
    'log in',
    'login',
    'email',
    'password',
    'username',
    'signin',
  ];
  
  const indicatorCount = loginIndicators.filter(indicator =>
    bodyText.includes(indicator)
  ).length;
  
  // If many login indicators and form elements, likely a login page
  const hasForm = $('form').length > 0;
  const hasEmailInput = $('input[type="email"], input[name="email"], input[name="username"]').length > 0;
  const hasPasswordInput = $('input[type="password"]').length > 0;
  
  return indicatorCount >= 3 && hasForm && hasEmailInput && hasPasswordInput;
}

function extractCompanyName($: cheerio.Root, url: string): string {
  // Try various sources for company name
  let name = $('meta[property="og:site_name"]').attr('content');
  if (name) return name;
  
  name = $('meta[name="application-name"]').attr('content');
  if (name) return name;
  
  name = $('h1').first().text().trim();
  if (name && name.length > 1 && name.length < 200) return name;
  
  const titleParts = $('title').text().split(/[|\-–]/);
  name = titleParts[0]?.trim() || '';
  if (name && name.length > 1 && name.length < 200) return name;
  
  // Extract from domain
  try {
    const domain = new URL(url).hostname;
    const domainName = domain.replace(/^www\./, '').split('.')[0];
    return domainName.charAt(0).toUpperCase() + domainName.slice(1);
  } catch {
    return '';
  }
}

function extractDescription($: cheerio.Root): string | undefined {
  let desc = $('meta[property="og:description"]').attr('content');
  if (desc) return desc.substring(0, 1000);
  
  desc = $('meta[name="description"]').attr('content');
  if (desc) return desc.substring(0, 1000);
  
  const aboutText = $('#about, .about, [class*="about"], section').first().text();
  if (aboutText && aboutText.length > 50) {
    return aboutText.substring(0, 1000).trim();
  }
  
  return undefined;
}

function extractEmployeeCount($: cheerio.Root): number | undefined {
  const text = $('body').text();
  
  // Match patterns like "50 employees", "50-200 employees", "About 50 people"
  const patterns = [
    /(\d[\d,]+)\s*(?:-\s*(\d[\d,]+))?\s*employees?/i,
    /(\d[\d,]+)\s*(?:-\s*(\d[\d,]+))?\s*people/i,
    /team of\s+(\d[\d,]+)/i,
    /(~)?(\d[\d,]+)\s*staff/i,
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      const count = parseInt(match[1].replace(/,/g, ''), 10);
      if (!isNaN(count) && count > 0 && count < 1000000) {
        return count;
      }
    }
  }
  
  return undefined;
}

function extractFoundedYear($: cheerio.Root): number | undefined {
  const text = $('body').text();
  
  // Match patterns like "Founded in 2020", "Since 2020", "2020"
  const patterns = [
    /founded\s+(?:in\s+)?(\d{4})/i,
    /since\s+(\d{4})/i,
    /(?:est\.?|established)\s*(?:in\s+)?(\d{4})/i,
    /\b(20\d{2}|19\d{2})\b/,
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      const year = parseInt(match[1], 10);
      if (year >= 1900 && year <= new Date().getFullYear()) {
        return year;
      }
    }
  }
  
  return undefined;
}

function extractPhone($: cheerio.Root): string | undefined {
  const text = $('body').text();
  
  // Match phone patterns
  const phonePattern = /\+?[\d\s\-().]{10,20}/g;
  const matches = text.match(phonePattern);
  
  if (matches) {
    // Filter out likely non-phone numbers
    const validPhones = matches.filter(m => {
      const digits = m.replace(/\D/g, '');
      return digits.length >= 10 && digits.length <= 15;
    });
    
    if (validPhones.length > 0) {
      return validPhones[0].trim();
    }
  }
  
  return undefined;
}

function extractEmail($: cheerio.Root): string | undefined {
  const text = $('body').text();
  
  // Match email pattern
  const emailPattern = /[\w.-]+@[\w.-]+\.\w+/g;
  const matches = text.match(emailPattern);
  
  if (matches) {
    // Filter out common non-contact emails
    const filtered = matches.filter(e =>
      !e.includes('noreply') &&
      !e.includes('no-reply') &&
      !e.includes('example') &&
      !e.includes('test')
    );
    
    if (filtered.length > 0) {
      return filtered[0].toLowerCase();
    }
  }
  
  return undefined;
}

function extractAddress($: cheerio.Root): string | undefined {
  // Look for address in common locations
  const addressSelectors = [
    '[class*="address"]',
    '[class*="location"]',
    '[class*="contact"]',
    'address',
  ];
  
  for (const selector of addressSelectors) {
    const element = $(selector).first();
    if (element.length) {
      const text = element.text().trim();
      if (text.length > 10 && text.length < 500) {
        return text;
      }
    }
  }
  
  return undefined;
}

function extractSocialLinks($: cheerio.Root): { linkedin?: string; twitter?: string; github?: string } {
  const links: { linkedin?: string; twitter?: string; github?: string } = {};
  
  $('a[href]').each((_, element) => {
    const href = $(element).attr('href') || '';
    const lowerHref = href.toLowerCase();
    
    if (lowerHref.includes('linkedin.com/company') || lowerHref.includes('linkedin.com/in')) {
      links.linkedin = href.startsWith('http') ? href : `https://${href}`;
    } else if (lowerHref.includes('twitter.com') || lowerHref.includes('x.com')) {
      links.twitter = href.startsWith('http') ? href : `https://${href}`;
    } else if (lowerHref.includes('github.com')) {
      links.github = href.startsWith('http') ? href : `https://${href}`;
    }
  });
  
  return links;
}

function detectTechStack($: cheerio.Root): string[] {
  const techStack: Set<string> = new Set();
  const content = $.html();
  
  // Technology indicators in HTML/script tags
  const techPatterns: Record<string, RegExp> = {
    'React': /react|reactjs|react\.js/i,
    'Vue.js': /vue\.js|vuejs|vue-js/i,
    'Angular': /angular|angularjs/i,
    'Node.js': /node\.js|nodejs|node-js/i,
    'Python': /python|django|flask/i,
    'Ruby': /ruby|rails|ruby-on-rails/i,
    'PHP': /php|laravel|symfony/i,
    'Java': /\bjava\b(?!script)/i,
    'JavaScript': /javascript|js\b/i,
    'TypeScript': /typescript|ts\b/i,
    'Go': /\bgo\b(?!ogle)|golang/i,
    'Rust': /\brust\b/i,
    '.NET': /\.net|dotnet/i,
    'AWS': /aws|amazon\s*web/i,
    'Google Cloud': /google\s*cloud|gcp/i,
    'Azure': /azure|microsoft\s*azure/i,
    'Docker': /docker|containerization/i,
    'Kubernetes': /kubernetes|k8s/i,
    'PostgreSQL': /postgresql|postgres/i,
    'MongoDB': /mongodb|mongo/i,
    'Redis': /redis/i,
    'GraphQL': /graphql/i,
    'REST API': /rest\s*api|restapi/i,
    'Next.js': /next\.js|nextjs/i,
    'Tailwind CSS': /tailwind/i,
    'WordPress': /wordpress|wp-content/i,
    'Shopify': /shopify/i,
    'Stripe': /stripe/i,
    'Twilio': /twilio/i,
    'Firebase': /firebase/i,
    'Supabase': /supabase/i,
  };
  
  for (const [tech, pattern] of Object.entries(techPatterns)) {
    if (pattern.test(content)) {
      techStack.add(tech);
    }
  }
  
  return Array.from(techStack);
}

export async function scrapeCompanyWebsite(
  url: string,
  industry: string,
  country: string,
  source?: string
): Promise<ScrapedCompany | null> {
  const domain = extractDomainFromUrl(url);
  
  if (!domain) {
    logger.warn('Invalid URL', { url });
    return null;
  }
  
  // Check robots.txt
  const robots = await checkRobotsTxt(domain);
  if (!robots.allowed) {
    logger.info('Scraping not allowed by robots.txt', { url });
    return null;
  }
  
  // Rate limiting per domain
  await delayForDomain(domain);
  
  const browserInstance = await getBrowser();
  const page = await browserInstance.newPage();
  
  try {
    await page.goto(url, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });
    
    // Check for login page
    const content = await page.content();
    if (isLoginPage(url, content)) {
      logger.info('Login page detected, skipping', { url });
      return null;
    }
    
    const $ = cheerio.load(content);
    
    // Extract data
    const company_name = extractCompanyName($, url);
    if (!company_name) {
      logger.warn('Could not extract company name', { url });
    }
    
    const description = extractDescription($);
    const employee_count = extractEmployeeCount($);
    const founded_year = extractFoundedYear($);
    const phone = extractPhone($);
    const primary_email = extractEmail($);
    const hq_address = extractAddress($);
    const socialLinks = extractSocialLinks($);
    const tech_stack = detectTechStack($);
    
    // Get page content for hashing
    const pageText = $('body').text().substring(0, 5000);
    const hash_homepage = hashContent(pageText);
    
    const company: ScrapedCompany = {
      company_name: company_name || '',
      website_url: url,
      domain,
      industry,
      country,
      description,
      employee_count,
      founded_year,
      phone,
      primary_email,
      hq_address,
      linkedin_url: socialLinks.linkedin,
      twitter_url: socialLinks.twitter,
      github_url: socialLinks.github,
      tech_stack,
      hash_homepage,
      sources: source ? [source] : [url],
    };
    
    logger.debug('Company scraped', {
      name: company_name,
      url,
      hasDescription: !!description,
      techCount: tech_stack.length,
    });
    
    return company;
    
  } catch (error) {
    if (error instanceof Error) {
      if (error.message.includes('404') || error.message.includes('Not Found')) {
        throw new NotFoundError(url);
      }
      if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        throw new AuthenticationError(url);
      }
      if (error.message.includes('429') || error.message.includes('Too Many Requests')) {
        throw new RateLimitError(url);
      }
    }
    
    throw new ScraperError(`Failed to scrape ${url}: ${(error as Error).message}`, {
      url,
      retryable: true,
    });
  } finally {
    await page.close();
  }
}

export async function scrapeMultipleCompanies(
  companies: Array<{ url: string; name?: string }>,
  industry: string,
  country: string
): Promise<ScrapedCompany[]> {
  const results: ScrapedCompany[] = [];
  
  logger.info('Starting batch scrape', {
    count: companies.length,
    industry,
    country,
  });
  
  for (const company of companies) {
    try {
      const scraped = await scrapeCompanyWebsite(company.url, industry, country, company.name);
      if (scraped) {
        results.push(scraped);
      }
    } catch (error) {
      logger.error('Failed to scrape company', {
        url: company.url,
        name: company.name,
        error: (error as Error).message,
      });
    }
    
    // Small delay between requests
    await randomDelay(1000, 2000);
  }
  
  logger.info('Batch scrape complete', {
    attempted: companies.length,
    successful: results.length,
  });
  
  return results;
}