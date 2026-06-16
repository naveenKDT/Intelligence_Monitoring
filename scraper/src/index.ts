import { loadConfig, AppConfig } from './config';
import { initializeDatabase } from './database/schema';
import { initializePool, query, closePool } from './database/connection';
import { discoverSources, closeBrowser as closeSourceBrowser } from './scraper/sourceDiscovery';
import { scrapeCompanyWebsite, closeBrowser as closeScraperBrowser } from './scraper/companyScraper';
import { extractDocumentsFromCompany } from './scraper/documentExtractor';
import { chunkDocument } from './embedding/chunker';
import { generateEmbedding, calculateEmbeddingStats } from './embedding/embedder';
import { upsertCompany, getCompanyCount, getDuplicateStats } from './storage/companyStorage';
import { storeDocumentWithChunks, getTotalDocumentCount, getTotalEmbeddingsCount } from './storage/documentStorage';
import { logger, LogLevel } from './utils/logger';
import { randomDelay, delayBetweenDomains } from './utils/delays';
import { handleError, formatErrorForStorage, ScraperError } from './utils/errors';
import * as cliProgress from 'cli-progress';
import chalk from 'chalk';

interface ScrapeJob {
  id: number;
  industry: string;
  country: string;
  status: string;
  companies_found: number;
  duplicates_removed: number;
  documents_collected: number;
  errors: unknown[];
  started_at: Date;
}

async function createScrapeJob(industry: string, country: string): Promise<number> {
  const result = await query<{ id: number }>(
    `INSERT INTO scrape_jobs (industry, country, status, started_at)
     VALUES ($1, $2, 'running', NOW())
     RETURNING id`,
    [industry, country]
  );
  
  return result.rows[0].id;
}

async function updateScrapeJob(
  jobId: number,
  updates: Partial<{
    status: string;
    companies_found: number;
    duplicates_removed: number;
    documents_collected: number;
    errors: unknown[];
    completed_at: Date;
  }>
): Promise<void> {
  const setClauses: string[] = [];
  const values: unknown[] = [];
  let paramIndex = 1;
  
  if (updates.status !== undefined) {
    setClauses.push(`status = $${paramIndex}`);
    values.push(updates.status);
    paramIndex++;
  }
  if (updates.companies_found !== undefined) {
    setClauses.push(`companies_found = $${paramIndex}`);
    values.push(updates.companies_found);
    paramIndex++;
  }
  if (updates.duplicates_removed !== undefined) {
    setClauses.push(`duplicates_removed = $${paramIndex}`);
    values.push(updates.duplicates_removed);
    paramIndex++;
  }
  if (updates.documents_collected !== undefined) {
    setClauses.push(`documents_collected = $${paramIndex}`);
    values.push(updates.documents_collected);
    paramIndex++;
  }
  if (updates.errors !== undefined) {
    setClauses.push(`errors = $${paramIndex}`);
    values.push(JSON.stringify(updates.errors));
    paramIndex++;
  }
  if (updates.completed_at !== undefined) {
    setClauses.push(`completed_at = $${paramIndex}`);
    values.push(updates.completed_at);
    paramIndex++;
  }
  
  if (setClauses.length === 0) return;
  
  values.push(jobId);
  await query(
    `UPDATE scrape_jobs SET ${setClauses.join(', ')} WHERE id = $${paramIndex}`,
    values
  );
}

async function getScrapeJob(jobId: number): Promise<ScrapeJob | null> {
  const result = await query<ScrapeJob>(
    'SELECT * FROM scrape_jobs WHERE id = $1',
    [jobId]
  );
  return result.rows[0] || null;
}

function printBanner(config: AppConfig): void {
  console.log(chalk.cyan(`
╔══════════════════════════════════════════════════════════════╗
║           B2B Company Web Scraper - Starting...              ║
╠══════════════════════════════════════════════════════════════╣
║  Industry: ${config.scraping.industry.padEnd(48)}║
║  Country:  ${config.scraping.country.padEnd(48)}║
╚══════════════════════════════════════════════════════════════╝
  `));
}

function printSummary(job: ScrapeJob, startTime: number): void {
  const duration = Math.round((Date.now() - startTime) / 1000);
  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  const seconds = duration % 60;
  
  console.log(chalk.green(`
╔══════════════════════════════════════════════════════════════╗
║                    Scraper Complete!                          ║
╠══════════════════════════════════════════════════════════════╣
║  Job ID:              ${String(job.id).padEnd(41)}║
║  Status:              ${job.status.padEnd(41)}║
║  Companies Found:     ${String(job.companies_found).padEnd(41)}║
║  Duplicates Merged:   ${String(job.duplicates_removed).padEnd(41)}║
║  Documents Collected: ${String(job.documents_collected).padEnd(41)}║
║  Duration:            ${`${hours}h ${minutes}m ${seconds}s`.padEnd(41)}║
╚══════════════════════════════════════════════════════════════╝
  `));
}

async function main(): Promise<void> {
  const startTime = Date.now();
  let config: AppConfig;
  let jobId: number = 0;
  const errors: unknown[] = [];
  
  try {
    // Load configuration
    logger.info('Loading configuration...');
    config = loadConfig();
    printBanner(config);
    
    // Initialize database
    logger.info('Initializing database...');
    await initializePool();
    await initializeDatabase();
    
    // Create scrape job
    logger.info('Creating scrape job...');
    jobId = await createScrapeJob(config.scraping.industry, config.scraping.country);
    logger.info('Scrape job created', { jobId });
    
    // Step 1: Discover sources
    console.log(chalk.blue('\n🔍 Discovering sources...'));
    const sources = await discoverSources(config.scraping.industry, config.scraping.country);
    console.log(chalk.green(`   Found ${sources.length} potential sources`));
    
    // Step 2: Scrape company websites
    console.log(chalk.blue('\n🕷️ Scraping company websites...'));
    const scrapedCompanies = [];
    const companyProgress = new cliProgress.SingleBar(
      {
        format: '   [{bar}] {percentage}% | {value}/{total} companies',
        barCompleteChar: '█',
        barIncompleteChar: '░',
      },
      cliProgress.Presets.shades_classic
    );
    
    companyProgress.start(sources.length, 0);
    
    for (let i = 0; i < sources.length; i++) {
      const source = sources[i];
      
      try {
        if (source.url && (source.type === 'company_website' || source.url.includes('linkedin.com'))) {
          const company = await scrapeCompanyWebsite(
            source.url,
            config.scraping.industry,
            config.scraping.country,
            source.url
          );
          
          if (company && company.company_name) {
            scrapedCompanies.push(company);
          }
        }
      } catch (error) {
        const err = handleError(error, { phase: 'scraping', url: source.url });
        errors.push({ ...formatErrorForStorage(err), url: source.url });
      }
      
      companyProgress.increment();
      
      // Rate limiting
      if (i < sources.length - 1) {
        await randomDelay(2000, 5000);
      }
    }
    
    companyProgress.stop();
    console.log(chalk.green(`   Scraped ${scrapedCompanies.length} companies`));
    
    // Step 3: Deduplicate and store companies
    console.log(chalk.blue('\n🔄 Deduplicating and storing companies...'));
    let newCompanies = 0;
    let duplicatesMerged = 0;
    
    for (const company of scrapedCompanies) {
      try {
        const result = await upsertCompany(company);
        if (result.isNew) {
          newCompanies++;
        } else {
          duplicatesMerged++;
        }
      } catch (error) {
        const err = handleError(error, { phase: 'deduplication', companyName: company.company_name });
        errors.push(formatErrorForStorage(err));
      }
    }
    
    console.log(chalk.green(`   New companies: ${newCompanies}`));
    console.log(chalk.green(`   Duplicates merged: ${duplicatesMerged}`));
    
    // Step 4: Extract documents and generate embeddings
    console.log(chalk.blue('\n📚 Extracting documents and generating embeddings...'));
    
    const companyCount = await getCompanyCount(config.scraping.industry, config.scraping.country);
    let totalDocuments = 0;
    let totalEmbeddings = 0;
    
    if (companyCount > 0) {
      // Get companies to process documents for
      const companies = await query<{ id: number; website_url: string; company_name: string }>(
        `SELECT id, website_url, company_name FROM companies 
         WHERE industry = $1 AND country = $2
         LIMIT 50`,
        [config.scraping.industry, config.scraping.country]
      );
      
      const docProgress = new cliProgress.SingleBar(
        {
          format: '   [{bar}] {percentage}% | {value}/{total} companies',
          barCompleteChar: '█',
          barIncompleteChar: '░',
        },
        cliProgress.Presets.shades_classic
      );
      
      docProgress.start(companies.rows.length, 0);
      
      for (const company of companies.rows) {
        try {
          // Extract documents
          const documents = await extractDocumentsFromCompany(
            company.website_url,
            config.scraping.industry
          );
          
          // Process each document
          for (const doc of documents.slice(0, 10)) { // Limit per company
            try {
              // Chunk the document
              const chunks = chunkDocument(doc.content, doc.url, doc.title);
              
              // Generate embeddings for chunks
              const chunksWithEmbeddings = [];
              for (const chunk of chunks.slice(0, 5)) { // Limit chunks per document
                try {
                  const result = await generateEmbedding(chunk.text);
                  if (result.embedding.length > 0) {
                    chunksWithEmbeddings.push({
                      chunk,
                      embedding: result.embedding,
                    });
                  }
                } catch {
                  // Skip failed embeddings
                }
              }
              
              // Store document with embeddings
              if (chunksWithEmbeddings.length > 0) {
                await storeDocumentWithChunks(company.id, doc, chunksWithEmbeddings);
                totalDocuments++;
                totalEmbeddings += chunksWithEmbeddings.length;
              }
            } catch {
              // Skip failed documents
            }
          }
          
          // Rate limiting
          await delayBetweenDomains();
          
        } catch (error) {
          const err = handleError(error, { phase: 'documents', companyName: company.company_name });
          errors.push(formatErrorForStorage(err));
        }
        
        docProgress.increment();
      }
      
      docProgress.stop();
    }
    
    console.log(chalk.green(`   Documents stored: ${totalDocuments}`));
    console.log(chalk.green(`   Embeddings generated: ${totalEmbeddings}`));
    
    // Update job status
    await updateScrapeJob(jobId, {
      status: 'completed',
      companies_found: newCompanies,
      duplicates_removed: duplicatesMerged,
      documents_collected: totalDocuments,
      errors: errors.slice(0, 100), // Store first 100 errors
      completed_at: new Date(),
    });
    
    // Print final summary
    const job = await getScrapeJob(jobId);
    if (job) {
      printSummary(job, startTime);
    }
    
    // Log to file
    logger.success('Scraper completed successfully', {
      jobId,
      newCompanies,
      duplicatesMerged,
      documentsCollected: totalDocuments,
      embeddingsGenerated: totalEmbeddings,
      duration: `${Date.now() - startTime}ms`,
    });
    
  } catch (error) {
    logger.error('Scraper failed', { error: (error as Error).message });
    
    if (jobId) {
      await updateScrapeJob(jobId, {
        status: 'failed',
        errors: [...errors, formatErrorForStorage(error)],
        completed_at: new Date(),
      });
    }
    
    throw error;
  } finally {
    // Cleanup
    await closeSourceBrowser();
    await closeScraperBrowser();
    await closePool();
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  logger.warn('Received SIGINT, shutting down gracefully...');
  await closePool();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.warn('Received SIGTERM, shutting down gracefully...');
  await closePool();
  process.exit(0);
});

// Run the scraper
main().catch((error) => {
  console.error(chalk.red('Fatal error:'), error);
  process.exit(1);
});