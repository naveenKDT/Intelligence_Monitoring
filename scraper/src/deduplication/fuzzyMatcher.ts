import Levenshtein from 'levenshtein';
import { normalize, extractDomainFromUrl } from './normalizer';
import { logger } from '../utils/logger';

export interface CompanyData {
  id?: number;
  company_name?: string;
  normalized_name?: string;
  website_url?: string;
  domain?: string;
  country?: string;
  region?: string;
  hq_address?: string;
  employee_count?: number;
  phone?: string;
  description?: string;
}

export interface MatchResult {
  isMatch: boolean;
  score: number;
  matchType: 'exact' | 'fuzzy' | 'domain' | 'composite';
  details: {
    nameSimilarity: number;
    domainMatch: number;
    locationMatch: number;
    employeeMatch: number;
  };
}

export function calculateNameSimilarity(name1: string, name2: string): number {
  const norm1 = normalize(name1);
  const norm2 = normalize(name2);
  
  if (norm1 === norm2) return 1;
  
  const distance = new Levenshtein(norm1, norm2).distance;
  const maxLength = Math.max(norm1.length, norm2.length);
  
  if (maxLength === 0) return 0;
  
  return 1 - distance / maxLength;
}

export function calculateDomainMatch(domain1: string, domain2: string): number {
  if (!domain1 || !domain2) return 0;
  
  const d1 = extractDomainFromUrl(domain1) || domain1;
  const d2 = extractDomainFromUrl(domain2) || domain2;
  
  if (d1 === d2) return 1;
  
  // Check if domains match after removing www and common prefixes
  const clean1 = d1.replace(/^www\./, '').replace(/^m\./, '');
  const clean2 = d2.replace(/^www\./, '').replace(/^m\./, '');
  
  if (clean1 === clean2) return 0.9;
  
  // Check if base domain matches (before TLD)
  const base1 = clean1.split('.').slice(0, -1).join('.');
  const base2 = clean2.split('.').slice(0, -1).join('.');
  
  if (base1 === base2) return 0.7;
  
  return 0;
}

export function calculateLocationMatch(
  addr1: string | undefined,
  addr2: string | undefined
): number {
  if (!addr1 || !addr2) return 0;
  
  const a1 = addr1.toLowerCase().trim();
  const a2 = addr2.toLowerCase().trim();
  
  if (a1 === a2) return 1;
  
  // Check for partial match on city/country
  const words1 = new Set(a1.split(/[\s,]+/));
  const words2 = new Set(a2.split(/[\s,]+/));
  
  const intersection = [...words1].filter(w => words2.has(w) && w.length > 3);
  
  if (intersection.length > 0) {
    return Math.min(intersection.length / Math.max(words1.size, words2.size), 0.5);
  }
  
  return 0;
}

export function calculateEmployeeMatch(
  count1: number | undefined,
  count2: number | undefined
): number {
  if (!count1 || !count2) return 0;
  if (count1 === count2) return 1;
  
  // Allow for similar company sizes
  const ratio = Math.min(count1, count2) / Math.max(count1, count2);
  
  if (ratio >= 0.8) return 0.5;
  if (ratio >= 0.5) return 0.2;
  
  return 0;
}

export function fuzzyMatch(company1: CompanyData, company2: CompanyData): MatchResult {
  const name1 = company1.company_name || company1.normalized_name || '';
  const name2 = company2.company_name || company2.normalized_name || '';
  
  // Layer 1: Exact match on normalized names
  const norm1 = normalize(name1);
  const norm2 = normalize(name2);
  
  if (norm1 === norm2) {
    return {
      isMatch: true,
      score: 1.0,
      matchType: 'exact',
      details: {
        nameSimilarity: 1,
        domainMatch: calculateDomainMatch(
          company1.website_url || company1.domain || '',
          company2.website_url || company2.domain || ''
        ),
        locationMatch: calculateLocationMatch(company1.hq_address, company2.hq_address),
        employeeMatch: calculateEmployeeMatch(company1.employee_count, company2.employee_count),
      },
    };
  }
  
  // Layer 2: Fuzzy matching
  const nameSimilarity = calculateNameSimilarity(name1, name2);
  const domainMatch = calculateDomainMatch(
    company1.website_url || company1.domain || '',
    company2.website_url || company2.domain || ''
  );
  const locationMatch = calculateLocationMatch(company1.hq_address, company2.hq_address);
  const employeeMatch = calculateEmployeeMatch(company1.employee_count, company2.employee_count);
  
  // Weighted composite score
  const score =
    nameSimilarity * 0.5 +
    domainMatch * 0.3 +
    locationMatch * 0.1 +
    employeeMatch * 0.1;
  
  // Determine match type
  let matchType: MatchResult['matchType'] = 'composite';
  if (domainMatch >= 0.9) {
    matchType = 'domain';
  } else if (nameSimilarity >= 0.85) {
    matchType = 'fuzzy';
  }
  
  return {
    isMatch: score >= 0.85,
    score,
    matchType,
    details: {
      nameSimilarity,
      domainMatch,
      locationMatch,
      employeeMatch,
    },
  };
}

export function findMatches(
  newCompany: CompanyData,
  existingCompanies: CompanyData[]
): Array<{ company: CompanyData; result: MatchResult }> {
  const matches: Array<{ company: CompanyData; result: MatchResult }> = [];
  
  for (const existing of existingCompanies) {
    const result = fuzzyMatch(newCompany, existing);
    
    if (result.isMatch) {
      matches.push({ company: existing, result });
    }
  }
  
  // Sort by score descending
  matches.sort((a, b) => b.result.score - a.result.score);
  
  return matches;
}

export function logMatchResult(result: MatchResult, company1: string, company2: string): void {
  if (result.isMatch) {
    logger.debug('Company match found', {
      company1,
      company2,
      score: result.score.toFixed(3),
      matchType: result.matchType,
      details: {
        nameSimilarity: result.details.nameSimilarity.toFixed(3),
        domainMatch: result.details.domainMatch.toFixed(3),
        locationMatch: result.details.locationMatch.toFixed(3),
        employeeMatch: result.details.employeeMatch.toFixed(3),
      },
    });
  }
}

export const MATCH_THRESHOLD = 0.85;
export const HIGH_CONFIDENCE_THRESHOLD = 0.95;
export const LOW_CONFIDENCE_THRESHOLD = 0.7;