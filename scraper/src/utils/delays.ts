import { logger } from './logger';

// Default delay ranges in milliseconds
const DEFAULT_MIN_DELAY = 2000;
const DEFAULT_MAX_DELAY = 5000;

// Store last request time per domain
const lastRequestTime: Map<string, number> = new Map();

// User agents for rotation
const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
];

let userAgentIndex = 0;

export function getRandomUserAgent(): string {
  userAgentIndex = (userAgentIndex + 1) % USER_AGENTS.length;
  return USER_AGENTS[userAgentIndex];
}

export function getRandomDelay(minMs?: number, maxMs?: number): number {
  const min = minMs ?? DEFAULT_MIN_DELAY;
  const max = maxMs ?? DEFAULT_MAX_DELAY;
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export async function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function randomDelay(minMs?: number, maxMs?: number): Promise<void> {
  const delayMs = getRandomDelay(minMs, maxMs);
  logger.debug(`Delaying for ${delayMs}ms`);
  return delay(delayMs);
}

export async function delayForDomain(
  domain: string,
  minMs?: number,
  maxMs?: number
): Promise<void> {
  const now = Date.now();
  const lastTime = lastRequestTime.get(domain);
  
  if (lastTime) {
    const elapsed = now - lastTime;
    const minDelay = minMs ?? DEFAULT_MIN_DELAY;
    
    if (elapsed < minDelay) {
      const waitTime = minDelay - elapsed;
      logger.debug(`Waiting ${waitTime}ms before requesting ${domain}`);
      await delay(waitTime);
    }
  }
  
  lastRequestTime.set(domain, Date.now());
}

export async function delayBetweenDomains(
  minMs?: number,
  maxMs?: number
): Promise<void> {
  const delayMs = getRandomDelay(minMs ?? 5000, maxMs ?? 10000);
  logger.debug(`Delaying ${delayMs}ms between domains`);
  return delay(delayMs);
}

export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000,
  maxDelayMs = 30000
): Promise<T> {
  let lastError: Error | undefined;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === maxRetries) {
        logger.error(`Max retries (${maxRetries}) reached`, {
          error: lastError.message,
        });
        throw lastError;
      }
      
      const delayMs = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
      logger.warn(`Retry ${attempt + 1}/${maxRetries} after ${delayMs}ms`, {
        error: lastError.message,
      });
      
      await delay(delayMs);
    }
  }
  
  throw lastError;
}

export function resetDelays(): void {
  lastRequestTime.clear();
  userAgentIndex = 0;
}

export function setDelays(minMs: number, maxMs: number): void {
  // This function can be used to override defaults via config
  logger.debug(`Delay range set to ${minMs}-${maxMs}ms`);
}