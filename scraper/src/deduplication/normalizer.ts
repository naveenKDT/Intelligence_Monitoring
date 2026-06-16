import { logger } from '../utils/logger';

// Legal entity suffixes to remove during normalization
const LEGAL_SUFFIXES = [
  'inc',
  'inc.',
  'corp',
  'corp.',
  'corporation',
  'ltd',
  'ltd.',
  'limited',
  'llc',
  'l.l.c.',
  'company',
  'co.',
  'co',
  'pvt',
  'pvt.',
  'private',
  'plc',
  'gmbh',
  'ag',
  'sa',
  'nv',
  'bv',
  'pty',
  'pty.',
  'pte',
  'pte.',
  'ltee',
  'ltee',
  'sarlu',
  'sarl',
  'sl',
  'slu',
  'overseas',
  'international',
  'enterprises',
  'solutions',
  'services',
  'group',
  ' holdings',
  ' technologies',
  ' tech',
  ' software',
  ' systems',
];

// Common words to remove
const COMMON_WORDS = [
  'the',
  'and',
  'of',
  'for',
  'in',
  'at',
  'by',
  'to',
  'a',
  'an',
  'with',
  'from',
];

export function normalize(name: string): string {
  if (!name) return '';

  let normalized = name
    // Convert to lowercase
    .toLowerCase()
    // Remove common legal suffixes
    .replace(
      new RegExp(`\\b(${LEGAL_SUFFIXES.join('|')})\\b`, 'gi'),
      ''
    )
    // Remove common words at the end
    .replace(
      new RegExp(`\\s+(${COMMON_WORDS.join('|')})\\s*$`, 'gi'),
      ''
    )
    // Replace multiple spaces with single space
    .replace(/\s+/g, ' ')
    // Remove punctuation except hyphens within words
    .replace(/[^\w\s-]/g, '')
    // Trim leading/trailing whitespace and hyphens
    .trim()
    .replace(/^-+|-+$/g, '');

  return normalized;
}

export function normalizeForComparison(name: string): string {
  const basic = normalize(name);
  // Additional aggressive normalization for comparison
  return basic
    .replace(/[^a-z0-9]/g, '')
    .toLowerCase();
}

export function extractDomainFromUrl(url: string): string {
  if (!url) return '';

  try {
    const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
    let domain = urlObj.hostname.toLowerCase();
    
    // Remove www. prefix
    if (domain.startsWith('www.')) {
      domain = domain.substring(4);
    }
    
    // Remove country-specific TLDs for comparison (e.g., .co.uk -> .com)
    domain = domain.replace(/\.co\.[a-z]{2}$/i, '.com');
    
    return domain;
  } catch {
    return '';
  }
}

export function extractDomainWithoutTld(domain: string): string {
  if (!domain) return '';
  
  const parts = domain.split('.');
  if (parts.length >= 2) {
    return parts.slice(0, -1).join('.');
  }
  return domain;
}

export interface NormalizedCompany {
  name: string;
  normalizedName: string;
  domain: string;
  domainWithoutTld: string;
}

export function normalizeCompany(
  name: string,
  url?: string
): NormalizedCompany {
  const normalizedName = normalize(name);
  const domain = url ? extractDomainFromUrl(url) : '';
  const domainWithoutTld = extractDomainWithoutTld(domain);

  return {
    name,
    normalizedName,
    domain,
    domainWithoutTld,
  };
}

export function isValidCompanyName(name: string): boolean {
  if (!name || name.length < 2) return false;
  
  // Must have at least one letter
  if (!/[a-zA-Z]/.test(name)) return false;
  
  // Should not be too long
  if (name.length > 200) return false;
  
  // Should not be only numbers
  if (/^\d+$/.test(name)) return false;
  
  return true;
}

export function cleanCompanyName(name: string): string {
  if (!name) return '';
  
  return name
    // Remove extra whitespace
    .replace(/\s+/g, ' ')
    .trim()
    // Capitalize first letter of each word
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

export function generateNameVariations(name: string): string[] {
  const variations: Set<string> = new Set();
  const base = normalize(name);
  
  variations.add(base);
  variations.add(normalizeForComparison(name));
  
  // Add with common prefixes
  const prefixes = ['', 'the ', 'the-'];
  for (const prefix of prefixes) {
    variations.add(normalize(prefix + name));
  }
  
  // Add without spaces
  variations.add(base.replace(/\s/g, ''));
  
  // Add with hyphen variations
  variations.add(base.replace(/\s/g, '-'));
  
  return Array.from(variations).filter(v => v.length > 0);
}

export function logNormalization(original: string, normalized: string): void {
  logger.debug('Company name normalized', {
    original,
    normalized,
    changed: original !== normalized,
  });
}