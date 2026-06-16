import { query, transaction } from '../database/connection';
import { normalize } from '../deduplication/normalizer';
import { fuzzyMatch, CompanyData } from '../deduplication/fuzzyMatcher';
import { hashContent } from '../deduplication/contentHash';
import { logger } from '../utils/logger';
import { ScrapedCompany } from '../scraper/companyScraper';

export interface CompanyRecord {
  id: number;
  company_name: string;
  normalized_name: string;
  website_url: string;
  domain: string;
  country: string;
  industry: string;
  description?: string;
  employee_count?: number;
  founded_year?: number;
  phone?: string;
  primary_email?: string;
  hq_address?: string;
  linkedin_url?: string;
  twitter_url?: string;
  github_url?: string;
  tech_stack: string[];
  hash_homepage?: string;
  sources: string[];
}

export interface UpsertResult {
  companyId: number;
  isNew: boolean;
  matchType?: 'exact' | 'fuzzy' | 'hash' | 'entity' | 'merged';
  matchScore?: number;
  deduplicated: boolean;
}

// Layer 1: Check exact match by normalized_name, country, and domain
async function checkExactMatch(
  normalizedName: string,
  country: string,
  domain: string
): Promise<CompanyRecord | null> {
  const result = await query<CompanyRecord>(
    `SELECT * FROM companies 
     WHERE normalized_name = $1 AND country = $2 AND domain = $3
     LIMIT 1`,
    [normalizedName, country, domain]
  );
  
  return result.rows[0] || null;
}

// Layer 2: Fuzzy match against similar companies
async function findSimilarCompanies(
  normalizedName: string,
  country: string,
  limit = 10
): Promise<CompanyRecord[]> {
  // Find companies with similar normalized names
  const result = await query<CompanyRecord>(
    `SELECT * FROM companies 
     WHERE country = $1 
     AND normalized_name % $2
     LIMIT $3`,
    [country, normalizedName, limit]
  );
  
  return result.rows;
}

// Layer 3: Check content hash
async function checkHashMatch(hash: string): Promise<CompanyRecord | null> {
  if (!hash) return null;
  
  const result = await query<CompanyRecord>(
    'SELECT * FROM companies WHERE hash_homepage = $1 LIMIT 1',
    [hash]
  );
  
  return result.rows[0] || null;
}

// Layer 4: Entity linking (simplified - look for similar domain patterns)
async function checkEntityMatch(
  normalizedName: string,
  domain: string,
  country: string
): Promise<CompanyRecord | null> {
  // Extract base domain (without TLD)
  const baseDomain = domain.split('.')[0];
  
  const result = await query<CompanyRecord>(
    `SELECT * FROM companies 
     WHERE country = $1 
     AND (domain LIKE $2 OR normalized_name LIKE $3)
     LIMIT 1`,
    [country, `%${baseDomain}%`, `%${baseDomain}%`]
  );
  
  return result.rows[0] || null;
}

export async function upsertCompany(company: ScrapedCompany): Promise<UpsertResult> {
  const normalizedName = normalize(company.company_name);
  const hash = company.hash_homepage || hashContent(company.website_url);
  
  // Layer 1: Exact match
  let existing = await checkExactMatch(normalizedName, company.country, company.domain);
  if (existing) {
    await mergeCompanyData(existing.id, company, 'exact', 1.0);
    return {
      companyId: existing.id,
      isNew: false,
      matchType: 'exact',
      matchScore: 1.0,
      deduplicated: true,
    };
  }
  
  // Layer 2: Fuzzy match
  const similarCompanies = await findSimilarCompanies(normalizedName, company.country);
  for (const candidate of similarCompanies) {
    const matchResult = fuzzyMatch(
      { ...candidate, company_name: candidate.company_name },
      { company_name: company.company_name, domain: company.domain }
    );
    
    if (matchResult.isMatch && matchResult.score >= 0.85) {
      await mergeCompanyData(candidate.id, company, 'fuzzy', matchResult.score);
      return {
        companyId: candidate.id,
        isNew: false,
        matchType: 'fuzzy',
        matchScore: matchResult.score,
        deduplicated: true,
      };
    }
  }
  
  // Layer 3: Content hash
  existing = await checkHashMatch(hash);
  if (existing) {
    await mergeCompanyData(existing.id, company, 'hash', 0.95);
    return {
      companyId: existing.id,
      isNew: false,
      matchType: 'hash',
      matchScore: 0.95,
      deduplicated: true,
    };
  }
  
  // Layer 4: Entity match
  existing = await checkEntityMatch(normalizedName, company.domain, company.country);
  if (existing) {
    await mergeCompanyData(existing.id, company, 'entity', 0.8);
    return {
      companyId: existing.id,
      isNew: false,
      matchType: 'entity',
      matchScore: 0.8,
      deduplicated: true,
    };
  }
  
  // No match found - insert new company
  const companyId = await insertCompany(company);
  
  return {
    companyId,
    isNew: true,
    deduplicated: false,
  };
}

async function mergeCompanyData(
  existingId: number,
  company: ScrapedCompany,
  matchType: string,
  matchScore: number
): Promise<void> {
  // Log the duplicate
  await query(
    `INSERT INTO duplicate_companies (primary_company_id, match_score, match_type)
     VALUES ($1, $2, $3)`,
    [existingId, matchScore, matchType]
  );
  
  // Merge sources
  await query(
    `UPDATE companies 
     SET sources = array_append(sources, $1),
         last_updated_at = NOW()
     WHERE id = $2
     AND NOT ($1 = ANY(sources))`,
    [company.website_url, existingId]
  );
  
  // Update other fields if empty
  const updates: string[] = [];
  const values: unknown[] = [];
  let paramIndex = 1;
  
  if (company.description && company.description.length > 0) {
    updates.push(`description = COALESCE(NULLIF(description, ''), $${paramIndex})`);
    values.push(company.description);
    paramIndex++;
  }
  if (company.employee_count) {
    updates.push(`employee_count = COALESCE(NULLIF(employee_count, 0), $${paramIndex})`);
    values.push(company.employee_count);
    paramIndex++;
  }
  if (company.founded_year) {
    updates.push(`founded_year = COALESCE(NULLIF(founded_year, 0), $${paramIndex})`);
    values.push(company.founded_year);
    paramIndex++;
  }
  if (company.phone) {
    updates.push(`phone = COALESCE(NULLIF(phone, ''), $${paramIndex})`);
    values.push(company.phone);
    paramIndex++;
  }
  if (company.primary_email) {
    updates.push(`primary_email = COALESCE(NULLIF(primary_email, ''), $${paramIndex})`);
    values.push(company.primary_email);
    paramIndex++;
  }
  if (company.hq_address) {
    updates.push(`hq_address = COALESCE(NULLIF(hq_address, ''), $${paramIndex})`);
    values.push(company.hq_address);
    paramIndex++;
  }
  if (company.linkedin_url) {
    updates.push(`linkedin_url = COALESCE(NULLIF(linkedin_url, ''), $${paramIndex})`);
    values.push(company.linkedin_url);
    paramIndex++;
  }
  if (company.twitter_url) {
    updates.push(`twitter_url = COALESCE(NULLIF(twitter_url, ''), $${paramIndex})`);
    values.push(company.twitter_url);
    paramIndex++;
  }
  if (company.github_url) {
    updates.push(`github_url = COALESCE(NULLIF(github_url, ''), $${paramIndex})`);
    values.push(company.github_url);
    paramIndex++;
  }
  if (company.tech_stack && company.tech_stack.length > 0) {
    updates.push(`tech_stack = COALESCE(NULLIF(array_length(tech_stack, 1), 0), $${paramIndex})`);
    values.push(company.tech_stack);
    paramIndex++;
  }
  
  if (updates.length > 0) {
    values.push(existingId);
    await query(
      `UPDATE companies SET ${updates.join(', ')}, last_updated_at = NOW() WHERE id = $${paramIndex}`,
      values
    );
  }
  
  logger.debug('Company data merged', {
    existingId,
    matchType,
    matchScore,
    updatesApplied: updates.length,
  });
}

async function insertCompany(company: ScrapedCompany): Promise<number> {
  const normalizedName = normalize(company.company_name);
  
  const result = await query<{ id: number }>(
    `INSERT INTO companies (
      company_name, normalized_name, website_url, domain, country, industry,
      description, employee_count, founded_year, phone, primary_email,
      hq_address, linkedin_url, twitter_url, github_url, tech_stack,
      hash_homepage, sources
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
    RETURNING id`,
    [
      company.company_name,
      normalizedName,
      company.website_url,
      company.domain,
      company.country,
      company.industry,
      company.description || null,
      company.employee_count || null,
      company.founded_year || null,
      company.phone || null,
      company.primary_email || null,
      company.hq_address || null,
      company.linkedin_url || null,
      company.twitter_url || null,
      company.github_url || null,
      company.tech_stack.length > 0 ? company.tech_stack : null,
      company.hash_homepage || null,
      company.sources.length > 0 ? company.sources : [company.website_url],
    ]
  );
  
  logger.info('New company inserted', {
    id: result.rows[0].id,
    name: company.company_name,
    domain: company.domain,
  });
  
  return result.rows[0].id;
}

export async function getCompanyById(id: number): Promise<CompanyRecord | null> {
  const result = await query<CompanyRecord>(
    'SELECT * FROM companies WHERE id = $1',
    [id]
  );
  return result.rows[0] || null;
}

export async function getCompanyCount(industry?: string, country?: string): Promise<number> {
  let queryText = 'SELECT COUNT(*) as count FROM companies';
  const params: unknown[] = [];
  
  if (industry || country) {
    const conditions: string[] = [];
    if (industry) {
      conditions.push(`industry = $${params.length + 1}`);
      params.push(industry);
    }
    if (country) {
      conditions.push(`country = $${params.length + 1}`);
      params.push(country);
    }
    queryText += ` WHERE ${conditions.join(' AND ')}`;
  }
  
  const result = await query<{ count: string }>(queryText, params);
  return parseInt(result.rows[0].count, 10);
}

export async function getDuplicateStats(): Promise<{
  totalDuplicates: number;
  byType: Record<string, number>;
}> {
  const result = await query<{ match_type: string; count: string }>(
    'SELECT match_type, COUNT(*) as count FROM duplicate_companies GROUP BY match_type'
  );
  
  const byType: Record<string, number> = {};
  let totalDuplicates = 0;
  
  for (const row of result.rows) {
    byType[row.match_type] = parseInt(row.count, 10);
    totalDuplicates += byType[row.match_type];
  }
  
  return { totalDuplicates, byType };
}

export async function searchCompanies(
  searchTerm: string,
  limit = 20
): Promise<CompanyRecord[]> {
  const result = await query<CompanyRecord>(
    `SELECT * FROM companies 
     WHERE company_name ILIKE $1 OR description ILIKE $1
     ORDER BY company_name
     LIMIT $2`,
    [`%${searchTerm}%`, limit]
  );
  
  return result.rows;
}

export async function getCompaniesByIndustry(
  industry: string,
  limit = 100,
  offset = 0
): Promise<CompanyRecord[]> {
  const result = await query<CompanyRecord>(
    `SELECT * FROM companies 
     WHERE industry = $1
     ORDER BY company_name
     LIMIT $2 OFFSET $3`,
    [industry, limit, offset]
  );
  
  return result.rows;
}

export async function getCompaniesByCountry(
  country: string,
  limit = 100,
  offset = 0
): Promise<CompanyRecord[]> {
  const result = await query<CompanyRecord>(
    `SELECT * FROM companies 
     WHERE country = $1
     ORDER BY company_name
     LIMIT $2 OFFSET $3`,
    [country, limit, offset]
  );
  
  return result.rows;
}