# Company & Industry Intelligence Platform

## Overview
AI-powered Company and Industry Intelligence Platform that continuously collects, organizes, analyzes, and monitors information about companies, industries, products, services, technologies, engineering domains, markets, customers, competitors, and business activities.

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
│   │   ├── api/              # API routes
│   │   ├── core/             # Core configuration
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── workers/          # Celery tasks
│   │   └── scraper/          # Web scraping
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