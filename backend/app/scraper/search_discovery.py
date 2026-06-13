"""
Search-Based Discovery
======================
Discovers companies using search engines (DuckDuckGo, Bing, etc.).
No API keys required for basic functionality.

Usage:
    from app.scraper.search_discovery import SearchDiscovery
    
    discoverer = SearchDiscovery()
    companies = discoverer.search("IoT company Germany")
    for company_url in companies:
        print(f"Found: {company_url}")
"""

import time
import random
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import re

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from app.config.industries import Industry, get_all_industries
from app.config.countries import Country, get_european_countries, get_country_by_code
from app.scraper.discovery_rules import DiscoveryRules, DiscoverySource


@dataclass
class DiscoveredCompany:
    """Represents a company discovered through search"""
    url: str
    source: str  # Which search/discovery source
    query: str  # The search query that found this
    industry: str  # The industry being searched
    country: str  # The country being searched
    title: Optional[str] = None  # Page title if available
    snippet: Optional[str] = None  # Search result snippet


class SearchDiscovery:
    """
    Discovers company URLs using search engines.
    Uses DuckDuckGo as primary (no API key needed).
    """
    
    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.session = requests.Session()
        
        # Common user agents to rotate
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        
        self.discovery_rules = DiscoveryRules()
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def search_duckduckgo(self, query: str, max_results: int = 20) -> List[DiscoveredCompany]:
        """
        Search using DuckDuckGo HTML (no API key needed).
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of DiscoveredCompany objects
        """
        self._rate_limit()
        
        companies = []
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # DuckDuckGo HTML results structure
            for result in soup.select('.result'):
                if len(companies) >= max_results:
                    break
                
                # Find the link
                link_elem = result.select_one('.result__a')
                if not link_elem:
                    continue
                
                link_url = link_elem.get('href', '')
                if not link_url or not self._is_valid_company_url(link_url):
                    continue
                
                # Get title
                title = link_elem.get_text(strip=True)
                
                # Get snippet
                snippet_elem = result.select_one('.result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                
                companies.append(DiscoveredCompany(
                    url=link_url,
                    source="DuckDuckGo",
                    query=query,
                    industry="",
                    country="",
                    title=title,
                    snippet=snippet
                ))
            
            # Also check for "More results" links
            for a in soup.select('.result__a'):
                link_url = a.get('href', '')
                if link_url and self._is_valid_company_url(link_url):
                    if not any(c.url == link_url for c in companies):
                        if len(companies) < max_results:
                            companies.append(DiscoveredCompany(
                                url=link_url,
                                source="DuckDuckGo",
                                query=query,
                                industry="",
                                country=""
                            ))
        
        except Exception as e:
            print(f"DuckDuckGo search error for '{query}': {e}")
        
        return companies
    
    def search_bing(self, query: str, max_results: int = 20) -> List[DiscoveredCompany]:
        """
        Search using Bing HTML.
        """
        self._rate_limit()
        
        companies = []
        url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            for result in soup.select('.b_algo'):
                if len(companies) >= max_results:
                    break
                
                link_elem = result.select_one('a')
                if not link_elem:
                    continue
                
                link_url = link_elem.get('href', '')
                if not link_url or not self._is_valid_company_url(link_url):
                    continue
                
                title = link_elem.get_text(strip=True)
                
                # Get snippet
                snippet_elem = result.select_one('.b_paractl')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                
                companies.append(DiscoveredCompany(
                    url=link_url,
                    source="Bing",
                    query=query,
                    industry="",
                    country="",
                    title=title,
                    snippet=snippet
                ))
        
        except Exception as e:
            print(f"Bing search error for '{query}': {e}")
        
        return companies
    
    def search_with_playwright(self, query: str, max_results: int = 20) -> List[DiscoveredCompany]:
        """
        Search using Playwright (for JavaScript-rendered pages).
        More reliable but slower.
        """
        companies = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    extra_http_headers={
                        "Accept-Language": "en-US,en;q=0.5",
                    }
                )
                page = context.new_page()
                
                # Try DuckDuckGo first
                url = f"https://duckduckgo.com/?q={requests.utils.quote(query)}&ia=web"
                page.goto(url, timeout=30000, wait_until="networkidle")
                
                # Wait for results
                page.wait_for_selector(".result__a", timeout=10000)
                
                # Extract results
                for result in page.query_selector_all(".result__a")[:max_results]:
                    href = result.get_attribute("href")
                    if href and self._is_valid_company_url(href):
                        title = result.inner_text().strip()
                        companies.append(DiscoveredCompany(
                            url=href,
                            source="DuckDuckGo (Playwright)",
                            query=query,
                            industry="",
                            country="",
                            title=title
                        ))
                
                browser.close()
        
        except Exception as e:
            print(f"Playwright search error for '{query}': {e}")
        
        return companies
    
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
            'microsoft.com', 'apple.com',  # Skip tech giants unless explicitly wanted
            'wordpress.com', 'blogspot.com', 'wix.com', 'squarespace.com',
            'gov', 'edu', 'org',  # Skip generic TLDs alone
        }
        
        # Check if domain ends with any skip domain
        for skip in skip_domains:
            if domain.endswith(skip) or domain == skip:
                # Allow linkedin company pages
                if 'linkedin.com/company/' in url and '/company/' in url:
                    continue
                return False
        
        # Skip URLs with common tracking parameters
        skip_patterns = ['/login', '/signup', '/register', '/search', 
                        '/cart', '/checkout', '/account', '/settings',
                        '/privacy', '/terms', '/contact']
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        return True
    
    def search(
        self, 
        query: str, 
        max_results: int = 20,
        use_playwright: bool = False
    ) -> List[DiscoveredCompany]:
        """
        Main search method - tries multiple engines.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            use_playwright: Use Playwright for better results (slower)
            
        Returns:
            List of discovered companies
        """
        if use_playwright:
            return self.search_with_playwright(query, max_results)
        
        # Try DuckDuckGo first (most reliable, no API key)
        companies = self.search_duckduckgo(query, max_results)
        
        # If no results, try Bing
        if not companies:
            companies = self.search_bing(query, max_results)
        
        return companies
    
    def discover_for_industry_country(
        self,
        industry: Industry,
        country: Country,
        max_results_per_query: int = 10,
        max_queries: int = 20
    ) -> List[DiscoveredCompany]:
        """
        Discover companies for a specific industry + country combination.
        This is the main entry point for the scraper.
        
        Args:
            industry: The industry to search
            country: The country to search in
            max_results_per_query: Max results per search query
            max_queries: Max number of search queries to run
            
        Returns:
            List of discovered companies
        """
        all_companies = []
        seen_urls: Set[str] = set()
        
        # Generate queries
        queries = self.discovery_rules.generate_queries(industry, country)
        
        # Limit queries to avoid too many requests
        queries_to_run = queries[:max_queries]
        
        for query in queries_to_run:
            if len(all_companies) >= max_results_per_query * len(queries_to_run):
                break
            
            print(f"  Searching: {query[:60]}...")
            
            # Run search
            companies = self.search(query, max_results=max_results_per_query)
            
            # Add industry/country info and dedupe
            for company in companies:
                if company.url not in seen_urls:
                    seen_urls.add(company.url)
                    company.industry = industry.name
                    company.country = country.code
                    all_companies.append(company)
            
            # Rate limit between queries
            time.sleep(random.uniform(1, 3))
        
        return all_companies
    
    def discover_batch(
        self,
        industries: List[Industry],
        countries: List[Country],
        max_results_per_query: int = 10,
        max_queries_per_combo: int = 10
    ) -> List[DiscoveredCompany]:
        """
        Discover companies for multiple industries and countries.
        
        Args:
            industries: List of industries to search
            countries: List of countries to search
            max_results_per_query: Max results per search query
            max_queries_per_combo: Max queries per industry+country combo
            
        Returns:
            List of all discovered companies
        """
        all_companies = []
        
        for industry in industries:
            for country in countries:
                print(f"\nDiscovering: {industry.name} in {country.name}...")
                
                companies = self.discover_for_industry_country(
                    industry=industry,
                    country=country,
                    max_results_per_query=max_results_per_query,
                    max_queries=max_queries_per_combo
                )
                
                all_companies.extend(companies)
                print(f"  Found {len(companies)} companies")
        
        return all_companies


# Singleton instance
search_discovery = SearchDiscovery()