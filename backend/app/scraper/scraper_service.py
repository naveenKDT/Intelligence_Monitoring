"""
Continuous Scraper Service
==========================
This service runs continuously in the background, scraping companies 24/7.
It can be run as a separate process: python run_scraper.py

The scraper uses dynamic discovery rules based on:
- Industries: IoT, Embedded Systems, Software, Automotive, etc.
- Countries: All European countries (configurable)

No hardcoded company URLs - everything is discovered dynamically!

Usage:
    python run_scraper.py                    # Run with default settings
    python run_scraper.py --workers 3        # Run with 3 concurrent workers
    python run_scraper.py --no-discovery     # Disable auto-discovery
    python run_scraper.py --limit 100        # Limit to 100 URLs
    python run_scraper.py --industries "IoT,Embedded"  # Filter by industries
    python run_scraper.py --countries "DE,FR,NL"       # Filter by countries
"""

import asyncio
import argparse
import signal
import sys
import time
from datetime import datetime
from typing import List, Optional, Dict, Set
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session
import httpx

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.models import Company, ScrapeQueue, ScrapeStatus

# Import new discovery modules
from app.config.industries import (
    get_all_industries, 
    get_industry_by_name, 
    Industry,
    INDUSTRY_ALIASES
)
from app.config.countries import (
    get_european_countries, 
    get_country_by_code,
    Country,
    COUNTRY_ALIASES
)
from app.scraper.discovery_rules import DiscoveryRules
from app.scraper.search_discovery import SearchDiscovery, DiscoveredCompany
from app.scraper.directory_discovery import DirectoryDiscovery


class ContinuousScraper:
    """
    Continuous scraper that runs 24/7, processing URLs from the queue.
    Uses dynamic discovery based on industry + country configurations.
    """
    
    # Discovery statistics
    discovery_stats = {
        'total_discovered': 0,
        'search_discovered': 0,
        'directory_discovered': 0,
        'queries_run': 0,
    }

    def __init__(
        self, 
        num_workers: int = 3, 
        enable_discovery: bool = True,
        industries: Optional[List[str]] = None,
        countries: Optional[List[str]] = None
    ):
        self.num_workers = num_workers
        self.enable_discovery = enable_discovery
        self.running = True
        self.scraped_count = 0
        self.error_count = 0
        
        # Initialize discovery components
        self.discovery_rules = DiscoveryRules()
        self.search_discovery = SearchDiscovery(rate_limit_seconds=2.0)
        self.directory_discovery = DirectoryDiscovery(rate_limit_seconds=3.0)
        
        # Load industry and country filters
        self.industries = self._load_industries(industries)
        self.countries = self._load_countries(countries)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_industries(self, industry_filter: Optional[List[str]]) -> List[Industry]:
        """Load industries based on filter or use all enabled"""
        all_industries = get_all_industries()
        
        if not industry_filter:
            return all_industries
        
        # Filter by provided names/aliases
        filtered = []
        for name in industry_filter:
            # Try direct match first
            industry = get_industry_by_name(name)
            if not industry:
                # Try alias resolution
                industry = next(
                    (i for i in all_industries if i.name.lower() == name.lower()),
                    None
                )
            if industry and industry not in filtered:
                filtered.append(industry)
        
        return filtered if filtered else all_industries
    
    def _load_countries(self, country_filter: Optional[List[str]]) -> List[Country]:
        """Load countries based on filter or use all European"""
        all_countries = get_european_countries()
        
        if not country_filter:
            return all_countries
        
        # Filter by provided codes/names
        filtered = []
        for code in country_filter:
            country = get_country_by_code(code)
            if not country:
                # Try name resolution
                country = next(
                    (c for c in all_countries if c.name.lower() == code.lower()),
                    None
                )
            if country and country not in filtered:
                filtered.append(country)
        
        return filtered if filtered else all_countries
    
    def _signal_handler(self, signum, frame):
        print("\n\nShutdown signal received. Finishing current tasks...")
        self.running = False
    
    def run(self):
        """Main loop - runs continuously"""
        print("=" * 70)
        print("  COMPANY INTELLIGENCE SCRAPER - DYNAMIC DISCOVERY")
        print("  Running continuously - Press Ctrl+C to stop")
        print("=" * 70)
        print(f"  Workers: {self.num_workers}")
        print(f"  Auto-discovery: {'Enabled' if self.enable_discovery else 'Disabled'}")
        print(f"  Industries: {len(self.industries)} ({', '.join(i.name for i in self.industries[:3])}{'...' if len(self.industries) > 3 else ''})")
        print(f"  Countries: {len(self.countries)} ({', '.join(c.name for c in self.countries[:3])}{'...' if len(self.countries) > 3 else ''})")
        print(f"  Ollama: {settings.OLLAMA_BASE_URL}")
        print("=" * 70)
        
        while self.running:
            try:
                # Process queue
                self._process_queue()
                
                # Auto-discover new URLs if enabled
                if self.enable_discovery:
                    self._discover_new_urls()
                
                # Small delay to prevent CPU spinning
                time.sleep(2)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(5)
        
        print(f"\n{'='*70}")
        print(f"Scraper stopped.")
        print(f"  Total scraped: {self.scraped_count}")
        print(f"  Total errors: {self.error_count}")
        print(f"  Total discovered: {self.discovery_stats['total_discovered']}")
        print(f"    - Via search: {self.discovery_stats['search_discovered']}")
        print(f"    - Via directories: {self.discovery_stats['directory_discovered']}")
        print(f"  Total queries run: {self.discovery_stats['queries_run']}")
        print("="*70)
    
    def _process_queue(self):
        """Process URLs from the scrape queue"""
        db = SessionLocal()
        try:
            # Get pending URLs ordered by priority
            pending_items = db.query(ScrapeQueue).filter(
                ScrapeQueue.status.in_([ScrapeStatus.PENDING, ScrapeStatus.QUEUED]),
                ScrapeQueue.retry_count < ScrapeQueue.max_retries
            ).order_by(
                ScrapeQueue.priority.desc(),
                ScrapeQueue.created_at.asc()
            ).limit(self.num_workers * 2).all()
            
            if not pending_items:
                return
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Queue: {len(pending_items)} items to process")
            
            # Process with thread pool
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = {
                    executor.submit(self._scrape_url, item.url, db): item
                    for item in pending_items
                }
                
                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        success = future.result()
                        if success:
                            self.scraped_count += 1
                        else:
                            self.error_count += 1
                    except Exception as e:
                        print(f"  Error processing {item.url}: {e}")
                        self.error_count += 1
            
            print(f"  Progress: {self.scraped_count} scraped, {self.error_count} errors")
            
        finally:
            db.close()
    
    def _scrape_url(self, url: str, db: Session) -> bool:
        """Scrape a single URL"""
        item = db.query(ScrapeQueue).filter(ScrapeQueue.url == url).first()
        if not item:
            return False
        
        # Mark as scraping
        item.status = ScrapeStatus.SCRAPING
        item.started_at = datetime.utcnow()
        db.commit()
        
        try:
            print(f"  Scraping: {url[:60]}...")
            
            # Perform scrape
            scraped_data = self._fetch_page(url)
            
            if not scraped_data:
                raise Exception("Failed to fetch page content")
            
            # Create or update company
            company = self._process_scraped_data(scraped_data, db)
            
            # Mark as completed
            item.status = ScrapeStatus.COMPLETED
            item.completed_at = datetime.utcnow()
            item.company_id = company.id if company else None
            db.commit()
            
            print(f"  ✓ Completed: {url[:50]}")
            
            # Extract links for future scraping
            if scraped_data.get('links'):
                self._queue_extracted_links(scraped_data['links'], db, url)
            
            return True
            
        except Exception as e:
            print(f"  ✗ Failed: {url[:50]} - {str(e)[:50]}")
            
            # Mark as failed or pending for retry
            item.retry_count += 1
            if item.retry_count >= item.max_retries:
                item.status = ScrapeStatus.FAILED
                item.error_message = str(e)
            else:
                item.status = ScrapeStatus.PENDING  # Retry later
            
            db.commit()
            return False
    
    def _fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch page content using requests + BeautifulSoup (more reliable)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 
                               'noscript', 'aside', 'iframe', 'svg', 'form']):
                element.decompose()
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else ''
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '').strip() if meta_desc else ''
            
            # Extract meta keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            keywords = meta_keywords.get('content', '').strip() if meta_keywords else ''
            
            # Get main content
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_=lambda x: x and any(c in str(x).lower() for c in ['content', 'main', 'article']))
            )
            
            if main_content:
                text_content = main_content.get_text(separator='\n', strip=True)
            else:
                body = soup.find('body')
                text_content = body.get_text(separator='\n', strip=True) if body else ''
            
            # Clean up text
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            text_content = '\n'.join(lines)[:50000]
            
            # Extract all links
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Skip empty, javascript, and anchor links
                if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    full_url = urljoin(url, href)
                    # Only include http/https links
                    if full_url.startswith('http'):
                        text = a.get_text(strip=True)
                        if text and len(text) < 200:
                            links.append({'url': full_url, 'text': text})
            
            # Extract images
            images = []
            for img in soup.find_all('img', src=True):
                src = urljoin(url, img['src'])
                alt = img.get('alt', '').strip()
                if src and not src.startswith('data:'):
                    images.append({'url': src, 'alt': alt})
            
            # Extract social links
            social_links = {
                'linkedin': None,
                'twitter': None,
                'facebook': None,
                'github': None,
            }
            
            for a in soup.find_all('a', href=True):
                href = a['href'].lower()
                if 'linkedin.com' in href and not social_links['linkedin']:
                    social_links['linkedin'] = a['href']
                elif 'twitter.com' in href and not social_links['twitter']:
                    social_links['twitter'] = a['href']
                elif 'facebook.com' in href and not social_links['facebook']:
                    social_links['facebook'] = a['href']
                elif 'github.com' in href and not social_links['github']:
                    social_links['github'] = a['href']
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'keywords': keywords,
                'text_content': text_content,
                'links': links[:200],
                'images': images[:50],
                'social_links': social_links,
                'status_code': response.status_code
            }
            
        except requests.exceptions.Timeout:
            print(f"    Timeout fetching {url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"    Request error: {e}")
            return None
        except Exception as e:
            print(f"    Error parsing {url}: {e}")
            return None
    
    def _process_scraped_data(self, data: Dict, db: Session) -> Optional[Company]:
        """Process scraped data and create/update company"""
        if not data.get('title') and not data.get('text_content'):
            return None
        
        try:
            # Check if company already exists
            existing = db.query(Company).filter(Company.website == data['url']).first()
            
            if existing:
                # Update existing company
                existing.name = data.get('title', existing.name)
                existing.description = data.get('description', existing.description)
                existing.short_description = data.get('description', '')[:1000]
                if data.get('text_content'):
                    metadata = existing.metadata or {}
                    metadata['scraped_content'] = data['text_content'][:100000]
                    metadata['last_scraped'] = datetime.utcnow().isoformat()
                    existing.metadata = metadata
                existing.last_scraped_at = datetime.utcnow()
                company = existing
            else:
                # Create new company
                company = Company(
                    name=data.get('title', 'Unknown Company'),
                    website=data.get('url'),
                    description=data.get('description'),
                    short_description=data.get('description', '')[:1000] if data.get('description') else None,
                    metadata={
                        'scraped_content': data.get('text_content', '')[:100000],
                        'keywords': data.get('keywords', ''),
                        'social_links': data.get('social_links', {}),
                        'first_scraped': datetime.utcnow().isoformat(),
                        'last_scraped': datetime.utcnow().isoformat(),
                    }
                )
                db.add(company)
            
            db.flush()  # Get the company ID
            
            # Extract location from content
            self._extract_location_info(company, data.get('text_content', ''))
            
            # Try to extract company info using simple heuristics
            self._extract_company_info(company, data.get('text_content', ''))
            
            db.commit()
            return company
            
        except Exception as e:
            print(f"    Error processing data: {e}")
            db.rollback()
            return None
    
    def _extract_location_info(self, company: Company, text: str):
        """Extract location information from text"""
        import re
        
        # Common country patterns
        countries = ['United States', 'USA', 'Germany', 'France', 'UK', 'United Kingdom', 
                    'Japan', 'China', 'India', 'Canada', 'Australia', 'Brazil', 'Mexico',
                    'Italy', 'Spain', 'Netherlands', 'Switzerland', 'Sweden', 'South Korea']
        
        for country in countries:
            if country.lower() in text.lower():
                company.country = country if country != 'USA' else 'United States'
                break
        
        # Common city patterns (simplified)
        cities = ['New York', 'San Francisco', 'Los Angeles', 'Chicago', 'Seattle',
                 'Boston', 'Austin', 'Denver', 'Berlin', 'Paris', 'London', 'Tokyo',
                 'Mumbai', 'Singapore', 'Sydney', 'Toronto', 'Vancouver']
        
        for city in cities:
            if city.lower() in text.lower():
                company.city = city
                break
    
    def _extract_company_info(self, company: Company, text: str):
        """Extract company information from text"""
        import re
        
        # Employee count patterns
        employee_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(?:employees|team members|staff)',
            r'company size[:\s]+(\d{1,3}(?:,\d{3})*)',
            r'we are\s*(\d{1,3}(?:,\d{3})*)\s*people',
        ]
        
        for pattern in employee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count = match.group(1).replace(',', '')
                if len(count) <= 6:  # Reasonable employee count
                    company.employee_range = f"{count}+ employees"
                    break
        
        # Founded year patterns
        year_pattern = r'(?:founded|established|since)\s*(?:in\s+)?(\d{4})'
        match = re.search(year_pattern, text, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            if 1800 <= year <= datetime.now().year:
                company.founded_year = year
    
    def _queue_extracted_links(self, links: List[Dict], db: Session, source_url: str):
        """Add extracted links to the scrape queue"""
        # Limit how many links we queue per page
        max_links = 20
        
        for link in links[:max_links]:
            url = link['url']
            
            # Skip if already in queue or recently scraped
            existing = db.query(ScrapeQueue).filter(ScrapeQueue.url == url).first()
            if existing:
                continue
            
            # Skip common non-company URLs
            skip_patterns = ['facebook.com', 'twitter.com', 'linkedin.com/company',
                           'youtube.com', 'instagram.com', 'pinterest.com',
                           'wordpress.com', 'blogspot.com', 'github.com/login']
            
            if any(pattern in url.lower() for pattern in skip_patterns):
                continue
            
            # Add to queue with low priority
            queue_item = ScrapeQueue(
                url=url,
                source='link_extraction',
                source_query=source_url,
                status=ScrapeStatus.PENDING,
                priority=3  # Lower priority than discovered URLs
            )
            db.add(queue_item)
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
    
    def _discover_new_urls(self):
        """
        Auto-discover new company URLs using dynamic discovery rules.
        Uses search engines and directories based on configured industries + countries.
        """
        db = SessionLocal()
        try:
            # Check how many pending items we have
            pending_count = db.query(ScrapeQueue).filter(
                ScrapeQueue.status.in_([ScrapeStatus.PENDING, ScrapeStatus.QUEUED])
            ).count()
            
            # If queue is running low, discover more URLs
            if pending_count < 50:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Queue running low ({pending_count}), starting discovery...")
                
                # Step 1: Search-based discovery
                self._discover_via_search(db)
                
                # Step 2: Directory-based discovery  
                self._discover_via_directories(db)
                
                print(f"  Discovery complete. Queue now has {db.query(ScrapeQueue).filter(ScrapeQueue.status.in_([ScrapeStatus.PENDING, ScrapeStatus.QUEUED])).count()} pending items")
                
        finally:
            db.close()
    
    def _discover_via_search(self, db: Session):
        """
        Discover companies using search engines (DuckDuckGo, Bing).
        This is the PRIMARY discovery method - generates queries dynamically.
        """
        print(f"\n  === Search-Based Discovery ===")
        
        discovered_urls: Set[str] = set()
        
        # Get already queued/scraped URLs to avoid duplicates
        existing_urls = set(
            url[0] for url in db.query(ScrapeQueue.url).all()
        )
        scraped_urls = set(
            url[0] for url in db.query(Company.website).filter(Company.website.isnot(None)).all()
        )
        discovered_urls = existing_urls | scraped_urls
        
        # Iterate through industry + country combinations
        for industry in self.industries:
            for country in self.countries:
                if not self.running:
                    break
                
                # Generate queries for this combination
                queries = self.discovery_rules.generate_queries(industry, country)
                
                print(f"  {industry.name} + {country.name}: {len(queries)} queries")
                
                # Run a few queries per combination (to avoid too many requests)
                queries_to_run = queries[:5]  # Limit queries per combo
                
                for query in queries_to_run:
                    if not self.running:
                        break
                    
                    self.discovery_stats['queries_run'] += 1
                    
                    try:
                        # Search for companies
                        companies = self.search_discovery.search(query, max_results=10)
                        
                        for company in companies:
                            if company.url in discovered_urls:
                                continue
                            
                            # Check if valid company URL
                            if not self._is_valid_company_url(company.url):
                                continue
                            
                            discovered_urls.add(company.url)
                            
                            # Queue the URL
                            queue_item = ScrapeQueue(
                                url=company.url,
                                source='search_discovery',
                                source_query=f"{industry.name}|{country.code}|{query}",
                                status=ScrapeStatus.QUEUED,
                                priority=industry.priority + country.priority,
                                metadata={
                                    'industry': industry.name,
                                    'country': country.code,
                                    'search_query': query,
                                    'search_source': company.source,
                                    'company_title': company.title,
                                }
                            )
                            db.add(queue_item)
                            self.discovery_stats['search_discovered'] += 1
                        
                        # Rate limit between queries
                        time.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        print(f"    Search error for query '{query[:40]}...': {e}")
                        continue
                
                # Small delay between industry combinations
                time.sleep(random.uniform(2, 4))
        
        try:
            db.commit()
            self.discovery_stats['total_discovered'] += self.discovery_stats['search_discovered']
            print(f"  Search discovery: {self.discovery_stats['search_discovered']} companies queued")
        except Exception as e:
            print(f"  Search discovery error: {e}")
            db.rollback()
    
    def _discover_via_directories(self, db: Session):
        """
        Discover companies from industry directories.
        This is a SECONDARY discovery method to supplement search.
        """
        print(f"\n  === Directory-Based Discovery ===")
        
        discovered_urls: Set[str] = set()
        
        # Get already queued/scraped URLs
        existing_urls = set(
            url[0] for url in db.query(ScrapeQueue.url).all()
        )
        scraped_urls = set(
            url[0] for url in db.query(Company.website).filter(Company.website.isnot(None)).all()
        )
        discovered_urls = existing_urls | scraped_urls
        
        directory_count = 0
        
        # Discover from industry-specific directories
        for industry in self.industries[:3]:  # Limit to avoid too many requests
            if not self.running:
                break
            
            try:
                entries = self.directory_discovery.discover_industry_specific(industry)
                
                for entry in entries:
                    if entry.url in discovered_urls:
                        continue
                    
                    if not self._is_valid_company_url(entry.url):
                        continue
                    
                    discovered_urls.add(entry.url)
                    
                    queue_item = ScrapeQueue(
                        url=entry.url,
                        source='directory_discovery',
                        source_query=f"{industry.name}|{entry.directory_name}",
                        status=ScrapeStatus.QUEUED,
                        priority=industry.priority,
                        metadata={
                            'industry': industry.name,
                            'directory': entry.directory_name,
                            'company_name': entry.name,
                        }
                    )
                    db.add(queue_item)
                    directory_count += 1
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"  Directory discovery error for {industry.name}: {e}")
        
        # Discover from European country-specific directories
        for country in self.countries[:3]:  # Top 3 countries
            if not self.running:
                break
            
            try:
                entries = self.directory_discovery.discover_european_industrial(country)
                
                for entry in entries:
                    if entry.url in discovered_urls:
                        continue
                    
                    if not self._is_valid_company_url(entry.url):
                        continue
                    
                    discovered_urls.add(entry.url)
                    
                    queue_item = ScrapeQueue(
                        url=entry.url,
                        source='directory_discovery',
                        source_query=f"{country.name}|{entry.directory_name}",
                        status=ScrapeStatus.QUEUED,
                        priority=country.priority,
                        metadata={
                            'country': country.name,
                            'country_code': country.code,
                            'directory': entry.directory_name,
                            'company_name': entry.name,
                        }
                    )
                    db.add(queue_item)
                    directory_count += 1
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"  Directory discovery error for {country.name}: {e}")
        
        try:
            db.commit()
            self.discovery_stats['directory_discovered'] = directory_count
            self.discovery_stats['total_discovered'] += directory_count
            print(f"  Directory discovery: {directory_count} companies queued")
        except Exception as e:
            print(f"  Directory commit error: {e}")
            db.rollback()
    
    def _is_valid_company_url(self, url: str) -> bool:
        """
        Check if a URL looks like a valid company website.
        Filters out social media, search engines, etc.
        """
        if not url:
            return False
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Skip social media and major platforms
        skip_domains = {
            'facebook.com', 'twitter.com', 'x.com', 'instagram.com',
            'linkedin.com', 'youtube.com', 'pinterest.com', 'tiktok.com',
            'snapchat.com', 'reddit.com', 'github.com', 'stackoverflow.com',
            'google.com', 'bing.com', 'duckduckgo.com', 'yahoo.com',
            'baidu.com', 'yandex.com',
            'amazon.com', 'ebay.com', 'aliexpress.com',
            'wikipedia.org', 'wikimedia.org',
            'microsoft.com', 'apple.com',
            'wordpress.com', 'blogspot.com', 'wix.com', 'squarespace.com',
        }
        
        for skip in skip_domains:
            if domain.endswith(skip) or domain == skip:
                # Allow linkedin company pages
                if 'linkedin.com/company/' in url and '/company/' in url:
                    continue
                return False
        
        # Skip URLs with common tracking parameters
        skip_patterns = ['/login', '/signup', '/register', '/search', 
                        '/cart', '/checkout', '/account', '/settings',
                        '/privacy', '/terms', '/contact', '/blog', '/news']
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Company Intelligence Scraper - Dynamic Discovery')
    parser.add_argument('--workers', type=int, default=3, help='Number of concurrent workers')
    parser.add_argument('--no-discovery', action='store_true', help='Disable auto-discovery')
    parser.add_argument('--limit', type=int, default=None, help='Limit total URLs to scrape')
    parser.add_argument('--industries', type=str, default=None, 
                       help='Comma-separated list of industries (e.g., "IoT,Embedded,Automotive")')
    parser.add_argument('--countries', type=str, default=None,
                       help='Comma-separated list of country codes (e.g., "DE,FR,NL")')
    
    args = parser.parse_args()
    
    # Parse industries and countries
    industries = args.industries.split(',') if args.industries else None
    countries = args.countries.split(',') if args.countries else None
    
    scraper = ContinuousScraper(
        num_workers=args.workers,
        enable_discovery=not args.no_discovery,
        industries=industries,
        countries=countries
    )
    
    scraper.run()


if __name__ == '__main__':
    main()