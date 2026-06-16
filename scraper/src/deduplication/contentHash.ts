import * as crypto from 'crypto';
import { logger } from '../utils/logger';

const MAX_CONTENT_LENGTH = 5000;
const NORMALIZE_CONTENT = true;

export function hashContent(content: string): string {
  if (!content) return '';
  
  let normalizedContent = content;
  
  if (NORMALIZE_CONTENT) {
    normalizedContent = normalizeForHashing(content);
  }
  
  // Take first MAX_CONTENT_LENGTH characters
  const truncated = normalizedContent.substring(0, MAX_CONTENT_LENGTH);
  
  return crypto.createHash('sha256').update(truncated).digest('hex');
}

function normalizeForHashing(content: string): string {
  return content
    // Convert to lowercase
    .toLowerCase()
    // Remove extra whitespace
    .replace(/\s+/g, ' ')
    // Remove common non-informative elements
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    // Remove HTML tags
    .replace(/<[^>]+>/g, ' ')
    // Remove URLs
    .replace(/https?:\/\/[^\s]+/g, '')
    // Remove email addresses
    .replace(/[\w.-]+@[\w.-]+\.\w+/g, '')
    // Remove phone numbers
    .replace(/\+?[\d\s\-().]{10,}/g, '')
    // Remove extra punctuation
    .replace(/[^\w\s]/g, '')
    // Trim
    .trim();
}

export function compareHashes(hash1: string, hash2: string): boolean {
  return hash1 === hash2 && hash1 !== '';
}

export function extractTextPreview(content: string, maxLength = 200): string {
  if (!content) return '';
  
  const normalized = normalizeForHashing(content);
  const cleaned = normalized
    .replace(/\s+/g, ' ')
    .trim();
  
  if (cleaned.length <= maxLength) {
    return cleaned;
  }
  
  return cleaned.substring(0, maxLength) + '...';
}

export interface HashVerification {
  matches: boolean;
  similarity: number;
  hash1: string;
  hash2: string;
}

export function verifyHashMatch(
  content1: string,
  content2: string
): HashVerification {
  const hash1 = hashContent(content1);
  const hash2 = hashContent(content2);
  
  return {
    matches: compareHashes(hash1, hash2),
    similarity: hash1 === hash2 ? 1 : 0,
    hash1,
    hash2,
  };
}

export function logHashInfo(content: string, hash: string): void {
  const preview = extractTextPreview(content);
  logger.debug('Content hashed', {
    hash,
    previewLength: preview.length,
    originalLength: content.length,
  });
}

export function isValidHash(hash: string): boolean {
  if (!hash) return false;
  if (hash.length !== 64) return false;
  return /^[a-f0-9]+$/.test(hash);
}

export function batchHash(contents: string[]): string[] {
  return contents.map(content => hashContent(content));
}

export function createHashLookup(companies: Array<{ id: number; hash_homepage?: string }>): Map<string, number> {
  const lookup = new Map<string, number>();
  
  for (const company of companies) {
    if (company.hash_homepage) {
      lookup.set(company.hash_homepage, company.id);
    }
  }
  
  logger.debug('Hash lookup table created', { size: lookup.size });
  return lookup;
}

export function findByHash(
  hash: string,
  lookup: Map<string, number>
): number | undefined {
  return lookup.get(hash);
}