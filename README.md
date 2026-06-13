# Company & Industry Intelligence Platform

## Overview
AI-powered Company and Industry Intelligence Platform that continuously collects, organizes, analyzes, and monitors information about companies, industries, products, services, technologies, engineering domains, markets, customers, competitors, and business activities.

## 🚀 NEW: Dynamic Discovery Architecture

The scraper now uses **dynamic discovery rules** instead of hardcoded URLs. Simply configure:
- **Industries**: IoT, Embedded Systems, Software, Automotive, etc.
- **Countries**: European countries (DE, FR, NL, BE, etc.)

The scraper automatically generates search queries and discovers companies!

### How It Works
```
┌─────────────────────────────────────────────────────────────────────┐
│                     DYNAMIC DISCOVERY ENGINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Config     │    │   Config     │    │   Discovery  │          │
│  │  Industries  │ +  │  Countries   │ →  │    Rules     │          │
│  │  (16 types)  │    │  (28 EU)     │    │  (Generates  │          │
│  └──────────────┘    └──────────────┘    │   queries)   │          │
│                                           └──────┬───────┘          │
│                                                  │                  │
│                          ┌───────────────────────┼───────────────┐ │
│                          ↓                       ↓               │ │
│                   ┌─────────────┐         ┌─────────────┐       │ │
│                   │   Search    │         │  Directory  │       │ │
│                   │ Discovery   │         │ Discovery   │       │ │
│                   │ (DuckDuckGo │         │ (ThomasNet  │       │ │
│                   │  Bing)      │         │  Europages) │       │ │
│                   └──────┬──────┘         └──────┬──────┘       │ │
│                          └───────────┬───────────┘               │ │
│                                      ↓                           │ │
│                               ┌──────────────┐                   │ │
│                               │ Scrape Queue │                   │ │
│                               │   + Queue    │                   │ │
│                               │   Workers    │                   │ │
│                               └──────┬───────┘                   │ │
│                                      ↓                           │ │
│                               ┌──────────────┐                   │ │
│                               │  Database    │                   │ │
│                               │  (PostgreSQL)│                   │ │
│                               └──────────────┘                   │ │
└─────────────────────────────────────────────────────────────────────┘
```

### Running the Scraper
```bash
# Run with all industries and European countries
python run_scraper.py

# Filter by specific industries
python run_scraper.py --industries "IoT,Embedded,Automotive"

# Filter by specific countries
python run_scraper.py --countries "DE,FR,NL"

# More workers for faster scraping
python run_scraper.py --workers 5

# Run as background daemon
python run_scraper.py --daemon
```

### Configured Industries (16 total)
- IoT (Internet of Things)
- Embedded Systems
- Software Development
- Semiconductors
- Automotive
- Automotive Electronics
- Industrial Automation
- Robotics
- Machine Vision
- Medical Devices
- Digital Health
- Renewable Energy
- Smart Grid
- Aerospace
- Agritech
- Telecommunications

### Configured Countries (28 European)
Germany (DE), France (FR), Netherlands (NL), Belgium (BE), Austria (AT), Switzerland (CH), Sweden (SE), Denmark (DK), Norway (NO), Finland (FI), Italy (IT), Spain (ES), Portugal (PT), Poland (PL), Czech Republic (CZ), Hungary (HU), Romania (RO), Greece (GR), Ireland (IE), United Kingdom (GB), Luxembourg (LU), Slovenia (SI), Slovakia (SK), Croatia (HR), Estonia (EE), Latvia (LV), Lithuania (LT), Bulgaria (BG)

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with pgvector
- **Background Processing**: Celery + Redis
- **AI**: Ollama (Qwen3 8B, Nomic Embed Text)

### Frontend
- **Framework**: React 18 with TypeScript
- **UI Library**: Material UI (MUI)
- **Data Grid**: AG Grid
- **Charts**: ECharts
- **State Management**: TanStack Query
- **Routing**: React Router v6

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Scraping**: Playwright, BeautifulSoup, Requests

## Features

### Data Collection
- [x] Website crawling and content extraction
- [x] Document extraction (PDFs, whitepapers)
- [x] Content normalization
- [x] Snapshot creation

### Intelligence
- [x] Company classification (industry, domain, technology)
- [x] Product and service extraction
- [x] Customer and partner identification
- [x] Leadership tracking
- [x] Market analysis

### Monitoring
- [x] Continuous company monitoring
- [x] Historical snapshots
- [x] Change detection
- [x] Alert generation

### Search & AI
- [x] Semantic search
- [x] Full-text search
- [x] AI-powered chat
- [x] Natural language queries

### Dashboards
- [x] Executive Dashboard
- [x] Industry Dashboard
- [x] Company Dashboard
- [x] Analytics Dashboard
- [x] Monitoring Dashboard

## Quick Start

### Prerequisites
- Docker and Docker Compose
- 16GB+ RAM (for Ollama)

### Development
```bash
# Start all services
docker-compose up -d

# Or for development with hot reload
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

### Access
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Ollama: http://localhost:11434

## API Endpoints

### Companies
- `GET /api/v1/companies` - List companies
- `POST /api/v1/companies` - Create company
- `GET /api/v1/companies/{id}` - Get company details
- `PUT /api/v1/companies/{id}` - Update company
- `DELETE /api/v1/companies/{id}` - Delete company

### Search
- `GET /api/v1/search` - Full-text and semantic search
- `GET /api/v1/search/companies` - Search companies by criteria
- `GET /api/v1/search/similar/{id}` - Find similar companies

### Intelligence
- `POST /api/v1/intelligence/extract` - Extract intelligence from content
- `POST /api/v1/intelligence/classify` - Classify company
- `GET /api/v1/intelligence/summary/{id}` - Get AI summary

### Monitoring
- `GET /api/v1/monitoring/companies` - Get monitored companies
- `POST /api/v1/monitoring/scrape` - Trigger scrape
- `GET /api/v1/monitoring/changes` - Get detected changes

### Dashboard
- `GET /api/v1/dashboard/executive` - Executive metrics
- `GET /api/v1/dashboard/industry` - Industry metrics
- `GET /api/v1/dashboard/company/{id}` - Company metrics

### Chat
- `POST /api/v1/chat` - AI chat about companies
- `GET /api/v1/chat/history/{company_id}` - Chat history

### Configuration (Discovery)
- `GET /api/v1/config/industries` - List all industries
- `GET /api/v1/config/industries/{name}` - Get industry details
- `GET /api/v1/config/countries` - List all countries
- `GET /api/v1/config/countries/europe` - List European countries
- `GET /api/v1/config/discovery/status` - Get discovery configuration
- `GET /api/v1/config/discovery/test-queries` - Test query generation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  React + TypeScript + MUI + AG Grid + ECharts               │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│                        Backend                               │
│  FastAPI + Python                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │  REST    │ │  Auth    │ │  Search  │                   │
│  │  APIs    │ │  JWT     │ │  pgvector │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Background Processing                      │
│  Celery + Redis                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Scraping │ │  AI      │ │ Embedding│ │ Monitoring│      │
│  │ Worker   │ │ Processing│ │ Worker   │ │ Worker   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     Data Layer                               │
│  PostgreSQL + pgvector                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ Company  │ │ Vector   │ │ Monitoring│                   │
│  │ Data     │ │ Store    │ │ History  │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                       AI Layer                               │
│  Ollama + Qwen3 8B + Nomic Embed Text                       │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
intelligence-platform/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes (including config for discovery)
│   │   ├── config/           # Industry & country configurations
│   │   │   ├── industries.py # 16 industries with search keywords
│   │   │   └── countries.py  # 28 European countries
│   │   ├── core/             # Core configuration
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── workers/          # Celery tasks
│   │   └── scraper/          # Web scraping with dynamic discovery
│   │       ├── discovery_rules.py    # Dynamic query generation
│   │       ├── search_discovery.py   # Search engine discovery
│   │       ├── directory_discovery.py# Directory-based discovery
│   │       ├── scraper.py            # Core scraping logic
│   │       └── scraper_service.py    # Continuous scraper service
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom hooks
│   │   ├── api/              # API client
│   │   └── utils/            # Utilities
│   └── package.json
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── README.md
```

## License
MIT