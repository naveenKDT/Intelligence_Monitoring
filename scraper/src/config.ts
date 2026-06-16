import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config();

export interface ScrapingConfig {
  industry: string;
  country: string;
}

export interface OpenAIConfig {
  apiKey: string;
}

export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
}

export interface AppConfig {
  scraping: ScrapingConfig;
  openai: OpenAIConfig;
  database: DatabaseConfig;
}

let cachedConfig: AppConfig | null = null;

export function loadConfig(configPath?: string): AppConfig {
  if (cachedConfig) {
    return cachedConfig;
  }

  const filePath = configPath || path.join(process.cwd(), 'config.json');
  
  if (!fs.existsSync(filePath)) {
    throw new Error(`Config file not found: ${filePath}`);
  }

  const configData = fs.readFileSync(filePath, 'utf-8');
  const config = JSON.parse(configData) as AppConfig;

  // Validate required fields
  validateConfig(config);

  // Override with environment variables if present
  if (process.env.OPENAI_API_KEY) {
    config.openai.apiKey = process.env.OPENAI_API_KEY;
  }
  if (process.env.DB_HOST) {
    config.database.host = process.env.DB_HOST;
  }
  if (process.env.DB_PORT) {
    config.database.port = parseInt(process.env.DB_PORT, 10);
  }
  if (process.env.DB_NAME) {
    config.database.database = process.env.DB_NAME;
  }
  if (process.env.DB_USER) {
    config.database.user = process.env.DB_USER;
  }
  if (process.env.DB_PASSWORD) {
    config.database.password = process.env.DB_PASSWORD;
  }
  if (process.env.SCRAPE_INDUSTRY) {
    config.scraping.industry = process.env.SCRAPE_INDUSTRY;
  }
  if (process.env.SCRAPE_COUNTRY) {
    config.scraping.country = process.env.SCRAPE_COUNTRY;
  }

  cachedConfig = config;
  return config;
}

function validateConfig(config: AppConfig): void {
  const errors: string[] = [];

  if (!config.scraping?.industry) {
    errors.push('Missing required field: scraping.industry');
  }
  if (!config.scraping?.country) {
    errors.push('Missing required field: scraping.country');
  }
  if (!config.openai?.apiKey) {
    errors.push('Missing required field: openai.apiKey');
  }
  if (!config.database?.host) {
    errors.push('Missing required field: database.host');
  }
  if (!config.database?.database) {
    errors.push('Missing required field: database.database');
  }
  if (!config.database?.user) {
    errors.push('Missing required field: database.user');
  }

  if (errors.length > 0) {
    throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
  }
}

export function getConfig(): AppConfig {
  if (!cachedConfig) {
    return loadConfig();
  }
  return cachedConfig;
}