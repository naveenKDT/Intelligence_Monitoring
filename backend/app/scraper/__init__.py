"""
Scraper Module
==============
Handles web scraping and company discovery.

Main components:
- scraper.py: Core scraping logic
- scraper_service.py: Continuous scraper service
- discovery_rules.py: Dynamic discovery rules engine
- search_discovery.py: Search-based company discovery
- directory_discovery.py: Directory-based company discovery
"""

# Import only the core scraper classes (not scraper_service to avoid circular imports)
from app.scraper.scraper import CompanyScraper, ContentExtractor, DocumentExtractor

__all__ = [
    # Core scraping
    "CompanyScraper",
    "ContentExtractor", 
    "DocumentExtractor",
]