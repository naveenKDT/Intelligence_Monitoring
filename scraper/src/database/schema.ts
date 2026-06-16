import { query } from './connection';
import { logger } from '../utils/logger';

const SCHEMA_SQL = `
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main companies table
CREATE TABLE IF NOT EXISTS companies (
  id BIGSERIAL PRIMARY KEY,
  company_name VARCHAR(255) NOT NULL,
  normalized_name VARCHAR(255) NOT NULL,
  website_url VARCHAR(500),
  domain VARCHAR(255),
  country VARCHAR(100) NOT NULL,
  region VARCHAR(100),
  industry VARCHAR(100) NOT NULL,
  sub_industries TEXT[],
  description TEXT,
  employee_count INT,
  founded_year INT,
  phone VARCHAR(20),
  primary_email VARCHAR(255),
  hq_address TEXT,
  office_locations JSONB,
  linkedin_url VARCHAR(500),
  twitter_url VARCHAR(500),
  github_url VARCHAR(500),
  tech_stack TEXT[],
  hash_homepage VARCHAR(64),
  first_scraped_at TIMESTAMP DEFAULT NOW(),
  last_updated_at TIMESTAMP DEFAULT NOW(),
  sources TEXT[] DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(normalized_name, country, domain)
);

-- Documents and embeddings
CREATE TABLE IF NOT EXISTS company_documents (
  id BIGSERIAL PRIMARY KEY,
  company_id BIGINT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  doc_type VARCHAR(50),
  title VARCHAR(500),
  url VARCHAR(500),
  content TEXT,
  published_date TIMESTAMP,
  scraped_at TIMESTAMP DEFAULT NOW(),
  embedding vector(1536),
  UNIQUE(company_id, url)
);

-- Track duplicates
CREATE TABLE IF NOT EXISTS duplicate_companies (
  id BIGSERIAL PRIMARY KEY,
  primary_company_id BIGINT REFERENCES companies(id),
  duplicate_company_id BIGINT REFERENCES companies(id),
  match_score FLOAT,
  match_type VARCHAR(50),
  merged_at TIMESTAMP DEFAULT NOW()
);

-- Scraping jobs log
CREATE TABLE IF NOT EXISTS scrape_jobs (
  id BIGSERIAL PRIMARY KEY,
  industry VARCHAR(100) NOT NULL,
  country VARCHAR(100) NOT NULL,
  status VARCHAR(20),
  companies_found INT DEFAULT 0,
  duplicates_removed INT DEFAULT 0,
  documents_collected INT DEFAULT 0,
  errors JSONB,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_company_name_country 
  ON companies USING GIN (to_tsvector('english', company_name));
CREATE INDEX IF NOT EXISTS idx_company_country 
  ON companies(country);
CREATE INDEX IF NOT EXISTS idx_company_industry 
  ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_domain 
  ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_normalized_name 
  ON companies(normalized_name);
CREATE INDEX IF NOT EXISTS idx_company_documents 
  ON company_documents(company_id);
CREATE INDEX IF NOT EXISTS idx_company_documents_embedding 
  ON company_documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status 
  ON scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_created 
  ON scrape_jobs(created_at DESC);
`;

export async function createSchema(): Promise<void> {
  logger.info('Creating database schema...');
  
  try {
    await query(SCHEMA_SQL);
    logger.info('Database schema created successfully');
  } catch (error) {
    logger.error('Failed to create schema', { error: (error as Error).message });
    throw error;
  }
}

export async function dropSchema(): Promise<void> {
  logger.warn('Dropping all database tables...');
  
  try {
    await query(`
      DROP TABLE IF EXISTS company_documents CASCADE;
      DROP TABLE IF EXISTS duplicate_companies CASCADE;
      DROP TABLE IF EXISTS companies CASCADE;
      DROP TABLE IF EXISTS scrape_jobs CASCADE;
    `);
    logger.info('Schema dropped successfully');
  } catch (error) {
    logger.error('Failed to drop schema', { error: (error as Error).message });
    throw error;
  }
}

export async function checkSchemaExists(): Promise<boolean> {
  try {
    const result = await query<{ exists: boolean }>(`
      SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'companies'
      ) as exists;
    `);
    return result.rows[0]?.exists ?? false;
  } catch {
    return false;
  }
}

export async function initializeDatabase(): Promise<void> {
  const exists = await checkSchemaExists();
  if (!exists) {
    await createSchema();
  } else {
    logger.info('Database schema already exists, skipping creation');
  }
}