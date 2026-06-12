# Technology Stack

## Frontend

Build the frontend using:

* React
* TypeScript
* Material UI
* AG Grid
* ECharts
* TanStack Query
* React Router

The UI must be modern, enterprise-grade, responsive, and optimized for large datasets.

The dashboard should provide:

* Executive dashboards
* Industry dashboards
* Company dashboards
* Analytics dashboards
* Monitoring dashboards
* AI search interface
* AI chat interface

---

## Backend

Build the backend using:

* Python
* FastAPI

Responsibilities:

* REST APIs
* Authentication
* Search APIs
* Company APIs
* Dashboard APIs
* Monitoring APIs
* AI APIs

The backend must be API-first.

---

## Background Processing

Build asynchronous processing using:

* Celery
* Redis

Responsibilities:

* Scraping jobs
* Monitoring jobs
* AI processing jobs
* Embedding generation
* Change detection
* Alert generation

---

## Scraping Layer

Build scraping services using:

* Playwright
* BeautifulSoup
* Requests

Responsibilities:

* Website crawling
* Content extraction
* Document extraction
* Content normalization
* Snapshot creation

---

## Database

Use:

* PostgreSQL

Store:

* Company data
* Industry data
* Domain data
* Product data
* Service data
* Customer data
* Partner data
* Leadership data
* News data
* Documents
* Monitoring history
* Snapshots
* Change history

---

## Vector Search

Use:

* PostgreSQL pgvector

Store embeddings for:

* Company descriptions
* Products
* Services
* Documents
* News
* Reports
* Industry summaries

Use pgvector for:

* Semantic search
* Similar company search
* AI chat
* Knowledge retrieval

---

## AI Layer

Run AI locally using:

* Ollama

Models:

* Qwen3 8B
* Nomic Embed Text

Responsibilities:

* Company classification
* Industry classification
* Domain classification
* Capability extraction
* Product extraction
* Service extraction
* Customer extraction
* Market extraction
* Competitor analysis
* Company summarization
* Industry summarization
* Semantic search
* AI chat

---

## Search

Implement:

* PostgreSQL Full Text Search
* pgvector Semantic Search

Support:

* Keyword search
* Semantic search
* Industry search
* Domain search
* Product search
* Capability search
* Similar company search

---

## Deployment

Containerize using:

* Docker
* Docker Compose

Services:

* Frontend
* Backend
* PostgreSQL
* Redis
* Ollama
* Celery Worker
* Celery Scheduler

---

## System Flow

Company Source
↓
Playwright Scraper
↓
Content Extraction
↓
PostgreSQL Raw Storage
↓
AI Processing (Qwen3)
↓
Classification
↓
Structured Data
↓
Embeddings (Nomic)
↓
pgvector
↓
Monitoring Snapshots
↓
Change Detection
↓
Dashboard & Search

---

## Scalability Goals

The platform should support:

* 100,000+ Companies
* Millions of Documents
* Millions of Embeddings
* Continuous Monitoring
* Real-time Search
* AI-powered Intelligence
* Multi-industry Analysis
* Industry Knowledge Graph
* Company Knowledge Graph
