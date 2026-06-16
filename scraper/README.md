# B2B Company Web Scraper

An automated web scraper that discovers, scrapes, deduplicates, and stores B2B company data with AI-powered embeddings.

## Features

- **Automatic Source Discovery** - No hardcoded URLs. Uses search queries to find company sources
- **4-Layer Deduplication** - Exact match, fuzzy match (Levenshtein), content hash, and entity linking
- **Document Extraction** - Extracts blogs, press releases, PDFs, and more
- **Vector Embeddings** - Uses OpenAI's text-embedding-3-small for semantic search
- **Rate Limiting** - Respects target servers with configurable delays
- **Robots.txt Compliance** - Checks and respects robots.txt files
- **Full Logging** - Timestamped logs to both console and files

## Prerequisites

- Node.js 18+
- Docker & Docker Compose (for PostgreSQL)
- OpenAI API Key

## Quick Start

### 1. Clone and Install

```bash
cd scraper
npm install
```

### 2. Configure

Edit `config.json` with your settings:

```json
{
  "scraping": {
    "industry": "SaaS",
    "country": "India"
  },
  "openai": {
    "apiKey": "sk-your-openai-api-key"
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "scraper_db",
    "user": "postgres",
    "password": "your-password"
  }
}
```

### 3. Start PostgreSQL

```bash
# Start PostgreSQL with pgvector
docker-compose up -d postgres

# Wait for database to be ready
sleep 5
```

### 4. Build and Run

```bash
# Build TypeScript
npm run build

# Run the scraper
npm run scrape
```

Or run directly with ts-node:

```bash
npm run dev
```

## Project Structure

```
scraper/
├── config.json           # Configuration file
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── docker-compose.yml    # PostgreSQL setup
├── .env.example          # Environment template
├── README.md
├── src/
│   ├── index.ts          # Main entry point
│   ├── config.ts         # Config loader
│   ├── database/
│   │   ├── connection.ts  # PostgreSQL connection pool
│   │   └── schema.ts     # Database schema
│   ├── scraper/
│   │   ├── sourceDiscovery.ts    # Auto-find sources
│   │   ├── companyScraper.ts     # Extract company data
│   │   └── documentExtractor.ts # Extract documents
│   ├── deduplication/
│   │   ├── normalizer.ts     # Company name normalization
│   │   ├── fuzzyMatcher.ts  # Levenshtein matching
│   │   ├── contentHash.ts   # SHA256 hashing
│   │   └── entityLinker.ts  # Entity resolution
│   ├── embedding/
│   │   ├── chunker.ts    # Document chunking
│   │   └── embedder.ts  # OpenAI embeddings
│   ├── storage/
│   │   ├── companyStorage.ts  # Company CRUD
│   │   └── documentStorage.ts # Document CRUD
│   └── utils/
│       ├── logger.ts    # Logging
│       ├── delays.ts    # Rate limiting
│       └── errors.ts    # Error handling
└── logs/                # Log files
```

## Database Schema

The scraper uses PostgreSQL with pgvector for vector storage:

### Tables

- `companies` - Main company data with deduplication support
- `company_documents` - Extracted documents with embeddings (vector(1536))
- `duplicate_companies` - Tracks duplicate detection
- `scrape_jobs` - Job history and statistics

### Indexes

- GIN index on company names for fast search
- ivfflat index on document embeddings for similarity search

## Configuration Options

### config.json

| Field | Description | Required |
|-------|-------------|----------|
| `scraping.industry` | Industry to search | Yes |
| `scraping.country` | Country to search | Yes |
| `openai.apiKey` | OpenAI API key | Yes |
| `database.host` | PostgreSQL host | Yes |
| `database.port` | PostgreSQL port | Yes |
| `database.database` | Database name | Yes |
| `database.user` | Database user | Yes |
| `database.password` | Database password | Yes |

### Environment Variables

You can override config values with environment variables:

```bash
export OPENAI_API_KEY=sk-...
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=scraper_db
export DB_USER=postgres
export DB_PASSWORD=secret
export SCRAPE_INDUSTRY=SaaS
export SCRAPE_COUNTRY=USA
```

## Deduplication Layers

The scraper uses 4 layers of deduplication:

1. **Exact Match** - Normalized name + country + domain
2. **Fuzzy Match** - Levenshtein distance with weighted scoring
3. **Content Hash** - SHA256 of homepage content
4. **Entity Linking** - Company name variations and acronyms

## Rate Limiting

- 2-5 second delay between requests to same domain
- 5-10 second delay between different domains
- Configurable via environment variables

## Logging

Logs are written to:
- Console (with timestamps and color)
- `logs/scrape-YYYY-MM-DD.log`

Log levels: DEBUG, INFO, WARN, ERROR

## API Usage

After running the scraper, you can query the database:

```sql
-- Get all companies
SELECT * FROM companies;

-- Find similar companies using embeddings
SELECT *, 
       1 - (embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM company_documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;

-- Get job statistics
SELECT * FROM scrape_jobs ORDER BY created_at DESC LIMIT 10;
```

## Troubleshooting

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker ps

# Start PostgreSQL
docker-compose up -d postgres

# Check logs
docker-compose logs postgres
```

### Playwright Not Working

```bash
# Install Playwright browsers
npx playwright install chromium
```

### Rate Limit Errors

The scraper automatically handles 429 errors with exponential backoff. If you see too many:

```bash
# Increase delays in config or environment
export REQUEST_DELAY_MIN_MS=3000
export REQUEST_DELAY_MAX_MS=8000
```

## License

MIT