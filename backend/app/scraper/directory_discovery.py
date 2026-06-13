"""
Directory-Based Discovery
==========================
Discovers companies from industry directories and databases.
These complement search-based discovery.

Usage:
    from app.scraper.directory_discovery import DirectoryDiscovery
    
    discoverer = DirectoryDiscovery()
    companies = discoverer.discover_from_all_industries()
"""

import time
import random
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin, quote_plus
import re

import requests
from bs4 import BeautifulSoup

from app.config.industries import Industry, get_all_industries, IndustryCategory
from app.config.countries import Country, get_european_countries, get_country_by_code, Region
from app.scraper.discovery_rules import DiscoveryRules, DiscoverySource
from app.scraper.search_discovery import DiscoveredCompany


@dataclass
class DirectoryEntry:
    """Represents a company found in a directory"""
    url: str
    name: str
    directory_name: str
    directory_url: str
    description: Optional[str] = None
    location: Optional[str] = None


class DirectoryDiscovery:
    """
    Discovers companies from industry directories.
    Each directory has its own structure and extraction logic.
    """
    
    def __init__(self, rate_limit_seconds: float = 3.0):
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.session = requests.Session()
        self.discovery_rules = DiscoveryRules()
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    
    def discover_thomasnet(self, country_code: str = "DE") -> List[DirectoryEntry]:
        """
        Discover companies from ThomasNet (industrial directory).
        """
        entries = []
        
        self._rate_limit()
        
        try:
            # ThomasNet has good coverage of industrial companies
            url = f"https://www.thomasnet.com/companies/{country_code.lower()}/"
            
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # ThomasNet company links typically have specific patterns
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Look for company profile links
                if '/company/' in href or '/profile/' in href:
                    full_url = urljoin(url, href)
                    if full_url not in [e.url for e in entries]:
                        if text and len(text) > 2:
                            entries.append(DirectoryEntry(
                                url=full_url,
                                name=text,
                                directory_name="ThomasNet",
                                directory_url=url
                            ))
        
        except Exception as e:
            print(f"ThomasNet discovery error: {e}")
        
        return entries
    
    def discover_crunchbase(self, query: str = "") -> List[DirectoryEntry]:
        """
        Discover companies from Crunchbase.
        Note: Crunchbase requires login for full access.
        """
        entries = []
        
        self._rate_limit()
        
        try:
            if query:
                url = f"https://www.crunchbase.com/discover/organization.companies?query={quote_plus(query)}"
            else:
                url = "https://www.crunchbase.com/discover/organization.companies"
            
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Crunchbase company links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/organization/' in href:
                    full_url = urljoin("https://www.crunchbase.com", href)
                    text = link.get_text(strip=True)
                    if text and full_url not in [e.url for e in entries]:
                        entries.append(DirectoryEntry(
                            url=full_url,
                            name=text,
                            directory_name="Crunchbase",
                            directory_url=url
                        ))
        
        except Exception as e:
            print(f"Crunchbase discovery error: {e}")
        
        return entries
    
    def discover_europages(self, industry: str, country_code: str = "DE") -> List[DirectoryEntry]:
        """
        Discover companies from Europages (European B2B directory).
        Good for finding European companies.
        """
        entries = []
        
        self._rate_limit()
        
        try:
            # Europages industry pages
            industry_slug = industry.lower().replace(" ", "-").replace("(", "").replace(")", "")
            url = f"https://www.europages.co.uk/{industry_slug}/{country_code.lower()}.html"
            
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Europages company links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/companies/' in href or '/company/' in href:
                    full_url = urljoin(url, href)
                    text = link.get_text(strip=True)
                    if text and full_url not in [e.url for e in entries]:
                        entries.append(DirectoryEntry(
                            url=full_url,
                            name=text,
                            directory_name="Europages",
                            directory_url=url
                        ))
        
        except Exception as e:
            print(f"Europages discovery error: {e}")
        
        return entries
    
    def discover_builtin(self, city: str = "berlin") -> List[DirectoryEntry]:
        """
        Discover tech companies from Built.in (by city).
        """
        entries = []
        
        self._rate_limit()
        
        try:
            url = f"https://www.builtin.com/companies/{city}"
            
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/company/' in href:
                    full_url = urljoin("https://www.builtin.com", href)
                    text = link.get_text(strip=True)
                    if text and full_url not in [e.url for e in entries]:
                        entries.append(DirectoryEntry(
                            url=full_url,
                            name=text,
                            directory_name=f"Builtin {city.title()}",
                            directory_url=url
                        ))
        
        except Exception as e:
            print(f"Builtin discovery error: {e}")
        
        return entries
    
    def discover_industry_specific(self, industry: Industry) -> List[DirectoryEntry]:
        """
        Discover companies from industry-specific directories.
        """
        entries = []
        
        # Map industry categories to directory URLs
        directory_map = {
            IndustryCategory.AUTOMOTIVE: [
                ("Automotive World", "https://www.automotiveworld.com/companies/"),
                ("Just Auto", "https://www.just-auto.com/companies/"),
            ],
            IndustryCategory.MANUFACTURING: [
                ("ThomasNet", "https://www.thomasnet.com/companies/"),
                ("Industry Week", "https://www.industryweek.com/companies"),
            ],
            IndustryCategory.TECHNOLOGY: [
                ("G2", f"https://www.g2.com/categories/{self.discovery_rules.get_industry_slug(industry)}"),
                ("Capterra", f"https://www.capterra.com/{self.discovery_rules.get_industry_slug(industry)}/"),
            ],
            IndustryCategory.HEALTHCARE: [
                ("MediWound", "https://www.meddeviceonline.com/company-directory"),
            ],
            IndustryCategory.ENERGY: [
                ("Greentech Media", "https://www.greentechmedia.com/company-directory"),
            ],
            IndustryCategory.AEROSPACE: [
                ("Aviation Week", "https://www.aviationweek.com/about-us/companies"),
            ],
        }
        
        for dir_name, dir_url in directory_map.get(industry.category, []):
            self._rate_limit()
            
            try:
                response = self.session.get(dir_url, headers=self._get_headers(), timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Look for company profile links (varies by site)
                    if any(pattern in href for pattern in ['/company/', '/profile/', '/member/', '/firm/']):
                        full_url = urljoin(dir_url, href)
                        if text and full_url not in [e.url for e in entries]:
                            entries.append(DirectoryEntry(
                                url=full_url,
                                name=text,
                                directory_name=dir_name,
                                directory_url=dir_url
                            ))
            
            except Exception as e:
                print(f"{dir_name} discovery error: {e}")
        
        return entries
    
    def discover_european_industrial(self, country: Country) -> List[DirectoryEntry]:
        """
        Discover industrial companies from European sources.
        """
        entries = []
        
        # European industrial directories by country
        european_dirs = {
            "DE": [  # Germany
                ("IndustryClub", "https://www.industryclub.de/unternehmen"),
                ("German Companies", "https://www.german-companies.com"),
            ],
            "FR": [  # France
                ("France Industrie", "https://www.france-industrie.org/nos-adherents"),
                ("French Tech", "https://Frenchtech.fr/en/companies"),
            ],
            "NL": [  # Netherlands
                ("FME", "https://www.fme.nl/leden"),
                ("DutchTech", "https://www.dutchequity.nl"),
            ],
            "SE": [  # Sweden
                ("Swedish Industry", "https://www.svenska-industrin.se"),
            ],
            "UK": [  # UK
                ("Make UK", "https://www.makeuk.org/abouts/members"),
                ("EEF", "https://www.eef.org.uk/members"),
            ],
        }
        
        dirs = european_dirs.get(country.code, [])
        
        for dir_name, dir_url in dirs:
            self._rate_limit()
            
            try:
                response = self.session.get(dir_url, headers=self._get_headers(), timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    if any(pattern in href for pattern in ['/company/', '/profile/', '/member/', '/company/']):
                        full_url = urljoin(dir_url, href)
                        if text and full_url not in [e.url for e in entries]:
                            entries.append(DirectoryEntry(
                                url=full_url,
                                name=text,
                                directory_name=dir_name,
                                directory_url=dir_url
                            ))
            
            except Exception as e:
                print(f"{dir_name} discovery error: {e}")
        
        return entries
    
    def discover_from_all_sources(self) -> List[DirectoryEntry]:
        """
        Discover companies from all configured directories.
        This is the main entry point for directory-based discovery.
        """
        all_entries = []
        
        print("Starting directory-based discovery...")
        
        # Get all enabled industries and countries
        industries = get_all_industries()
        countries = get_european_countries()
        
        # Discover from industry-specific directories
        for industry in industries[:5]:  # Limit to avoid too many requests
            print(f"  Discovering from {industry.name} directories...")
            entries = self.discover_industry_specific(industry)
            all_entries.extend(entries)
            time.sleep(random.uniform(2, 4))
        
        # Discover from European directories
        for country in countries[:5]:  # Top 5 countries
            print(f"  Discovering from {country.name} directories...")
            entries = self.discover_european_industrial(country)
            all_entries.extend(entries)
            time.sleep(random.uniform(2, 4))
        
        # Deduplicate
        seen_urls = set()
        unique_entries = []
        for entry in all_entries:
            if entry.url not in seen_urls:
                seen_urls.add(entry.url)
                unique_entries.append(entry)
        
        print(f"Directory discovery complete: {len(unique_entries)} unique companies")
        
        return unique_entries
    
    def convert_to_discovered_companies(self, entries: List[DirectoryEntry]) -> List[DiscoveredCompany]:
        """Convert DirectoryEntry objects to DiscoveredCompany for scraping"""
        return [
            DiscoveredCompany(
                url=entry.url,
                source=f"Directory: {entry.directory_name}",
                query=entry.directory_url,
                industry="",
                country="",
                title=entry.name,
                snippet=entry.description
            )
            for entry in entries
        ]


# Singleton instance
directory_discovery = DirectoryDiscovery()