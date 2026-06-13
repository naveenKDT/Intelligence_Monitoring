"""
Continuous Scraper Service
==========================
This service runs continuously in the background, scraping companies 24/7.
It can be run as a separate process: python run_scraper.py

Usage:
    python run_scraper.py                    # Run with default settings
    python run_scraper.py --workers 3        # Run with 3 concurrent workers
    python run_scraper.py --no-discovery     # Disable auto-discovery
    python run_scraper.py --limit 100        # Limit to 100 URLs
"""

import asyncio
import argparse
import signal
import sys
import time
from datetime import datetime
from typing import List, Optional, Dict
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


class ContinuousScraper:
    """
    Continuous scraper that runs 24/7, processing URLs from the queue.
    """
    
    def __init__(self, num_workers: int = 3, enable_discovery: bool = True):
        self.num_workers = num_workers
        self.enable_discovery = enable_discovery
        self.running = True
        self.scraped_count = 0
        self.error_count = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n\nShutdown signal received. Finishing current tasks...")
        self.running = False
    
    def run(self):
        """Main loop - runs continuously"""
        print("=" * 60)
        print("  COMPANY INTELLIGENCE SCRAPER")
        print("  Running continuously - Press Ctrl+C to stop")
        print("=" * 60)
        print(f"  Workers: {self.num_workers}")
        print(f"  Auto-discovery: {'Enabled' if self.enable_discovery else 'Disabled'}")
        print(f"  Ollama: {settings.OLLAMA_BASE_URL}")
        print("=" * 60)
        
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
        
        print(f"\nScraper stopped. Total scraped: {self.scraped_count}, Errors: {self.error_count}")
    
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
        """Auto-discover new company URLs to scrape"""
        db = SessionLocal()
        try:
            # Check how many pending items we have
            pending_count = db.query(ScrapeQueue).filter(
                ScrapeQueue.status.in_([ScrapeStatus.PENDING, ScrapeStatus.QUEUED])
            ).count()
            
            # If queue is running low, add more URLs
            if pending_count < 50:
                self._discover_from_industry_sources(db)
                self._discover_from_search(db)
                
        finally:
            db.close()
    
    def _discover_from_industry_sources(self, db: Session):
        """Discover companies from industry directories and sources"""
        # Industry-specific sources to discover companies
        discovery_sources = [
            # Technology & Software
            {'url': 'https://www.builtin.com/companies', 'industry': 'Technology'},
            {'url': 'https://crunchbase.com/discover/organization.companies', 'industry': 'Technology'},
            
            # Industrial & Manufacturing
            {'url': 'https://www.thomasnet.com/companies/', 'industry': 'Manufacturing'},
            
            # Auto & Automotive
            {'url': 'https://www.automotiveworld.com/companies/', 'industry': 'Automotive'},
            
            # General business directories
            {'url': 'https://www.yellowpages.com', 'industry': 'General'},
        ]
        
        for source in random.sample(discovery_sources, min(2, len(discovery_sources))):
            try:
                response = requests.get(source['url'], timeout=10)
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Find company links
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    text = a.get_text(strip=True)
                    
                    # Look for company links (usually start with /company/ or /firm/)
                    if '/company/' in href or '/firm/' in href:
                        url = urljoin(source['url'], href)
                        
                        # Check if already in queue
                        existing = db.query(ScrapeQueue).filter(ScrapeQueue.url == url).first()
                        if existing:
                            continue
                        
                        # Add to queue
                        queue_item = ScrapeQueue(
                            url=url,
                            source='discovery',
                            source_query=source['industry'],
                            status=ScrapeStatus.QUEUED,
                            priority=5
                        )
                        db.add(queue_item)
                
                db.commit()
                
            except Exception as e:
                print(f"    Discovery error from {source['url']}: {e}")
                db.rollback()
    
    def _discover_from_search(self, db: Session):
        """Discover companies using search queries"""
        # Search queries for different industries
        search_queries = [
            'site:.com company about automation robotics',
            'site:.com industrial IoT solutions',
            'site:.com automotive technology company',
            'site:.com medical device manufacturer',
            'site:.com aerospace engineering company',
            'site:.com renewable energy company',
            'site:.com manufacturing automation',
            'site:.com embedded systems company',
        ]
        
        # Note: In production, you would use a search API (Google, Bing)
        # For now, we'll add some seed URLs from known company lists
        
        seed_companies = [
            # Tech companies
            'https://www.siemens.com',
            'https://www.bosch.com',
            'https://www.abb.com',
            'https://www.schneider-electric.com',
            'https://www.emerson.com',
            'https://www.rockwellautomation.com',
            'https://wwwHoneywell.com',
            'https://www.ge.com',
            # Automotive
            'https://www.bosch-mobility.com',
            'https://www.denso.com',
            'https://www.continental.com',
            'https://www ZF.com',
            # Industrial
            'https://www.fanuc.com',
            'https://www.kuka.com',
            'https://www. YASKAWA.com',
            'https://www.mitsubishi-electric.com',
            # Medical
            'https://www.medtronic.com',
            'https://www.siemens-healthineers.com',
            'https://www.gehealthcare.com',
            # Aerospace
            'https://www Boeing.com',
            'https://www Airbus.com',
            'https://www Lockheedmartin.com',
            'https://www.raytheon.com',
        ]
        
        for url in random.sample(seed_companies, min(10, len(seed_companies))):
            existing = db.query(ScrapeQueue).filter(ScrapeQueue.url == url).first()
            if existing:
                continue
            
            queue_item = ScrapeQueue(
                url=url,
                source='discovery',
                source_query='industry_seed',
                status=ScrapeStatus.QUEUED,
                priority=7  # Higher priority for seed URLs
            )
            db.add(queue_item)
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()


def main():
    parser = argparse.ArgumentParser(description='Company Intelligence Scraper')
    parser.add_argument('--workers', type=int, default=3, help='Number of concurrent workers')
    parser.add_argument('--no-discovery', action='store_true', help='Disable auto-discovery')
    parser.add_argument('--limit', type=int, default=None, help='Limit total URLs to scrape')
    
    args = parser.parse_args()
    
    scraper = ContinuousScraper(
        num_workers=args.workers,
        enable_discovery=not args.no_discovery
    )
    
    scraper.run()


if __name__ == '__main__':
    main()