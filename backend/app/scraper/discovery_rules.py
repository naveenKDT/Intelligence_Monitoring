"""
Discovery Rules Engine
======================
Dynamic discovery rules for finding companies based on industry + country.
This replaces hardcoded URLs with dynamic query generation.

How it works:
1. Given an industry + country combination
2. Generate search queries (not hardcoded URLs)
3. Use search engines and directories to find companies
4. Queue discovered URLs for scraping

Usage:
    from app.scraper.discovery_rules import DiscoveryRules
    
    rules = DiscoveryRules()
    queries = rules.generate_queries(industry, country)
    discovery_sources = rules.get_discovery_sources(industry, country)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urljoin
import random

from app.config.industries import Industry, IndustryCategory
from app.config.countries import Country, Region


@dataclass
class DiscoverySource:
    """
    Represents a source for discovering companies.
    """
    name: str
    source_type: str  # 'search', 'directory', 'api', 'list'
    url_template: str  # URL template with placeholders like {query}, {country}, {industry}
    
    # How to extract company links from this source
    link_pattern: str = ""  # CSS selector or XPath for finding company links
    
    # Whether this source is enabled
    enabled: bool = True
    
    # Priority (higher = more important)
    priority: int = 5
    
    # Rate limiting (requests per minute)
    rate_limit: int = 30
    
    # Description
    description: str = ""


@dataclass
class DiscoveryRule:
    """
    A discovery rule that generates queries and sources for an industry + country.
    """
    name: str
    industry: Industry
    country: Optional[Country] = None  # None means all countries
    
    # Search query templates
    query_templates: List[str] = field(default_factory=list)
    
    # Discovery sources specific to this rule
    sources: List[DiscoverySource] = field(default_factory=list)
    
    # Whether this rule is enabled
    enabled: bool = True
    
    # Priority for this rule
    priority: int = 5


class DiscoveryRules:
    """
    Core discovery rules engine.
    Generates dynamic discovery queries and sources based on industry + country.
    """
    
    def __init__(self):
        self._init_search_sources()
        self._init_directory_sources()
        self._init_api_sources()
    
    def _init_search_sources(self):
        """Initialize search engine sources"""
        self.search_sources: List[DiscoverySource] = [
            DiscoverySource(
                name="DuckDuckGo",
                source_type="search",
                url_template="https://duckduckgo.com/?q={query}&ia=web",
                link_pattern=".result__a",
                priority=10,
                rate_limit=20,
                description="DuckDuckGo search engine - no API key needed"
            ),
            DiscoverySource(
                name="Bing",
                source_type="search",
                url_template="https://www.bing.com/search?q={query}",
                link_pattern=".b_algo a",
                priority=8,
                rate_limit=15,
                description="Microsoft Bing search"
            ),
            DiscoverySource(
                name="Google (via SerpAPI)",
                source_type="search_api",
                url_template="https://serpapi.com/search.json?q={query}&engine=google",
                priority=9,
                rate_limit=10,
                description="Google search via SerpAPI (requires API key)"
            ),
            DiscoverySource(
                name="Bing Search API",
                source_type="search_api",
                url_template="https://api.bing.microsoft.com/v7.0/search?q={query}",
                priority=7,
                rate_limit=10,
                description="Bing Search API (requires API key)"
            ),
        ]
    
    def _init_directory_sources(self):
        """Initialize industry directory sources"""
        self.directory_sources: List[DiscoverySource] = [
            # Technology Directories
            DiscoverySource(
                name="Builtin Cities",
                source_type="directory",
                url_template="https://www.builtin.com/companies/{city}",
                link_pattern=".company-card a, .company-listing a",
                priority=7,
                description="Tech company directory by city"
            ),
            DiscoverySource(
                name="Crunchbase",
                source_type="directory",
                url_template="https://www.crunchbase.com/discover/organization.companies?query={industry}",
                link_pattern=".cb-cell-company-name a",
                priority=8,
                rate_limit=10,
                description="Business information directory"
            ),
            DiscoverySource(
                name="G2",
                source_type="directory",
                url_template="https://www.g2.com/categories/{industry_slug}",
                link_pattern=".product-listing a, .edge-listing a",
                priority=7,
                description="Software and technology reviews"
            ),
            DiscoverySource(
                name="Capterra",
                source_type="directory",
                url_template="https://www.capterra.com/{industry_slug}/",
                link_pattern=".location-title a, .vendor-info a",
                priority=6,
                description="Software comparison directory"
            ),
            
            # Industrial Directories
            DiscoverySource(
                name="ThomasNet",
                source_type="directory",
                url_template="https://www.thomasnet.com/companies/{country_code}/",
                link_pattern=".company-name a, .distributor-name a",
                priority=8,
                description="Industrial manufacturer directory"
            ),
            DiscoverySource(
                name="IndustryWeek",
                source_type="directory",
                url_template="https://www.industryweek.com/companies",
                link_pattern=".card-title a, .company-link",
                priority=6,
                description="Manufacturing industry directory"
            ),
            
            # IoT & Embedded Directories
            DiscoverySource(
                name="IoT World Today",
                source_type="directory",
                url_template="https://www.iotworldtoday.com/company-directory",
                link_pattern=".company-listing a, .directory-item a",
                priority=7,
                description="IoT company directory"
            ),
            DiscoverySource(
                name="Embedded Computing Design",
                source_type="directory",
                url_template="https://www.embedded-computing.com/company-list",
                link_pattern=".company-link, .member-link",
                priority=6,
                description="Embedded systems company directory"
            ),
            
            # Automotive Directories
            DiscoverySource(
                name="Automotive World",
                source_type="directory",
                url_template="https://www.automotiveworld.com/companies/",
                link_pattern=".company-name a, .exhibitor-link",
                priority=8,
                description="Automotive industry directory"
            ),
            DiscoverySource(
                name="Just Auto",
                source_type="directory",
                url_template="https://www.just-auto.com/companies/",
                link_pattern=".company-name a",
                priority=7,
                description="Automotive industry news and directory"
            ),
            
            # European Directories
            DiscoverySource(
                name="Europages",
                source_type="directory",
                url_template="https://www.europages.co.uk/{industry_slug}/{country_code}.html",
                link_pattern=".companyName a, .ep-company-name a",
                priority=8,
                description="European B2B directory"
            ),
            DiscoverySource(
                name="German Trade Fair (AUMA)",
                source_type="directory",
                url_template="https://www.auma.de/en/exhibitors",
                link_pattern=".exhibitor-list a, .company-link",
                priority=6,
                description="German trade fair exhibitor database"
            ),
            
            # Robotics Directories
            DiscoverySource(
                name="Robotics Business Review",
                source_type="directory",
                url_template="https://www.roboticsbusinessreview.com/company-directory/",
                link_pattern=".company-name a, .roster-link",
                priority=7,
                description="Robotics company directory"
            ),
            DiscoverySource(
                name="International Federation of Robotics",
                source_type="directory",
                url_template="https://ifr.org/members",
                link_pattern=".member-link, .company-name a",
                priority=6,
                description="IFR robot manufacturer members"
            ),
            
            # Medical Device Directories
            DiscoverySource(
                name="MediWound",
                source_type="directory",
                url_template="https://www.meddeviceonline.com/company-directory",
                link_pattern=".company-link",
                priority=7,
                description="Medical device company directory"
            ),
            DiscoverySource(
                name="FDA 510(k) Database",
                source_type="database",
                url_template="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm",
                link_pattern=".result-row a",
                priority=8,
                description="FDA medical device approvals database"
            ),
            
            # Agricultural Directories
            DiscoverySource(
                name="AgriTech Tomorrow",
                source_type="directory",
                url_template="https://www.agritechtomorrow.com/company-directory/",
                link_pattern=".company-link, .member-company a",
                priority=6,
                description="Agritech company directory"
            ),
            
            # Energy Directories
            DiscoverySource(
                name="Greentech Media",
                source_type="directory",
                url_template="https://www.greentechmedia.com/company-directory",
                link_pattern=".company-link, .member-name a",
                priority=7,
                description="Clean energy company directory"
            ),
        ]
    
    def _init_api_sources(self):
        """Initialize API-based sources"""
        self.api_sources: List[DiscoverySource] = [
            DiscoverySource(
                name="OpenCorporates",
                source_type="api",
                url_template="https://api.opencorporates.com/v0.8/companies/search?q={query}&jurisdiction_code={country_code}",
                priority=7,
                rate_limit=10,
                description="Open database of company information"
            ),
            DiscoverySource(
                name="Companies House (UK)",
                source_type="api",
                url_template="https://api.companieshouse.gov.uk/search/companies?q={query}",
                priority=8,
                rate_limit=10,
                description="UK company registration data"
            ),
        ]
    
    def generate_queries(self, industry: Industry, country: Country) -> List[str]:
        """
        Generate search queries for an industry + country combination.
        This is the CORE function - generates queries dynamically based on config.
        
        Returns a list of search queries that can be used with search engines.
        """
        queries = []
        
        # Base keywords from industry config
        for keyword in industry.search_keywords:
            # Basic queries
            queries.append(f"{keyword} company {country.name}")
            queries.append(f"{keyword} {country.name}")
            
            # With company type indicators
            queries.append(f"{keyword} manufacturer {country.name}")
            queries.append(f"{keyword} solutions {country.name}")
            queries.append(f"{keyword} technology {country.name}")
            queries.append(f"{keyword} systems {country.name}")
            
            # Specific to country variations
            for alt_name in country.search_names[:2]:
                if alt_name != country.name:
                    queries.append(f"{keyword} {alt_name}")
                    queries.append(f"{keyword} company {alt_name}")
        
        # Sub-industry queries (limit to avoid too many)
        for sub in industry.sub_industries[:3]:
            queries.append(f"{sub} {country.name}")
            queries.append(f"{sub} company {country.name}")
        
        # Domain-specific queries (country TLD)
        if country.tld:
            queries.append(f'site:.{country.tld} {industry.name}')
            queries.append(f'site:.{country.tld} {industry.search_keywords[0]}')
        
        # Company suffix queries (common in European company names)
        for suffix in industry.company_suffixes:
            queries.append(f'"{suffix}" {industry.search_keywords[0]} {country.name}')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)
        
        return unique_queries
    
    def generate_queries_batch(self, industries: List[Industry], countries: List[Country]) -> List[Tuple[Industry, Country, str]]:
        """
        Generate queries for all industry + country combinations.
        Returns tuples of (industry, country, query).
        """
        results = []
        for industry in industries:
            for country in countries:
                queries = self.generate_queries(industry, country)
                for query in queries:
                    results.append((industry, country, query))
        return results
    
    def get_discovery_sources(self, industry: Industry, country: Country) -> List[DiscoverySource]:
        """
        Get relevant discovery sources for an industry + country combination.
        """
        sources = []
        
        # Add search sources (always relevant)
        for source in self.search_sources:
            if source.enabled:
                sources.append(source)
        
        # Add relevant directory sources based on industry
        industry_keywords = [k.lower() for k in industry.search_keywords]
        
        for source in self.directory_sources:
            if not source.enabled:
                continue
            
            # Check if source is relevant to this industry
            source_relevant = False
            
            # Check by name
            source_name_lower = source.name.lower()
            for keyword in industry_keywords:
                if keyword in source_name_lower or any(k in source_name_lower for k in industry_keywords):
                    source_relevant = True
                    break
            
            # Check by industry category
            if industry.category == IndustryCategory.AUTOMOTIVE:
                if 'automotive' in source_name_lower or 'auto' in source_name_lower:
                    source_relevant = True
            elif industry.category == IndustryCategory.MANUFACTURING:
                if 'industrial' in source_name_lower or 'manufacturing' in source_name_lower:
                    source_relevant = True
            elif industry.category == IndustryCategory.HEALTHCARE:
                if 'medical' in source_name_lower or 'health' in source_name_lower:
                    source_relevant = True
            elif industry.category == IndustryCategory.ENERGY:
                if 'energy' in source_name_lower or 'tech media' in source_name_lower:
                    source_relevant = True
            elif industry.category == IndustryCategory.TECHNOLOGY:
                if 'tech' in source_name_lower or 'software' in source_name_lower:
                    source_relevant = True
            
            if source_relevant or source.priority >= 7:
                sources.append(source)
        
        # Sort by priority
        sources.sort(key=lambda s: s.priority, reverse=True)
        
        # Deduplicate
        seen = set()
        unique_sources = []
        for s in sources:
            if s.name not in seen:
                seen.add(s.name)
                unique_sources.append(s)
        
        return unique_sources[:10]  # Limit to top 10 sources
    
    def get_search_url(self, source: DiscoverySource, query: str) -> str:
        """Generate a search URL from a template"""
        return source.url_template.replace("{query}", quote_plus(query))
    
    def get_industry_slug(self, industry: Industry) -> str:
        """Generate URL slug from industry name"""
        return industry.name.lower().replace(" ", "-").replace("(", "").replace(")", "")
    
    def get_all_queries_for_scrape_session(self, industries: List[Industry], countries: List[Country]) -> List[Dict]:
        """
        Generate a complete list of queries for a scraping session.
        Returns dicts with industry, country, query, and priority.
        """
        session_queries = []
        
        for industry in industries:
            for country in countries:
                queries = self.generate_queries(industry, country)
                for query in queries:
                    session_queries.append({
                        "industry": industry.name,
                        "country": country.code,
                        "query": query,
                        "priority": industry.priority + country.priority,
                    })
        
        # Sort by priority (highest first)
        session_queries.sort(key=lambda x: x["priority"], reverse=True)
        
        return session_queries


# Singleton instance
discovery_rules = DiscoveryRules()