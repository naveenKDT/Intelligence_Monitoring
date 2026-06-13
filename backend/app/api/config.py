"""
Industries and Countries API
============================
API endpoints for managing industries and countries used in discovery.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.config.industries import (
    INDUSTRIES, 
    get_all_industries, 
    get_industry_by_name,
    get_industry_by_category,
    get_all_industry_names,
    get_all_sub_industries,
    resolve_industry_alias,
    Industry,
    IndustryCategory
)
from app.config.countries import (
    COUNTRIES, 
    get_all_countries, 
    get_european_countries,
    get_country_by_code,
    get_country_by_name,
    get_countries_by_region,
    get_all_country_names,
    resolve_country_alias,
    Country,
    Region
)


router = APIRouter(prefix="/config", tags=["Configuration"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class IndustryBase(BaseModel):
    name: str
    category: str
    sub_industries: List[str]
    search_keywords: List[str]
    enabled: bool
    priority: int
    description: str


class IndustryResponse(IndustryBase):
    id: str  # Using name as ID
    
    class Config:
        from_attributes = True


class CountryBase(BaseModel):
    name: str
    code: str
    region: str
    languages: List[str]
    tld: str
    enabled: bool
    priority: int
    description: str


class CountryResponse(CountryBase):
    pass


class IndustryListResponse(BaseModel):
    industries: List[IndustryResponse]
    total: int
    categories: List[str]


class CountryListResponse(BaseModel):
    countries: List[CountryResponse]
    total: int
    regions: List[str]


class DiscoveryStatusResponse(BaseModel):
    industries: List[str]
    countries: List[str]
    total_industries: int
    total_countries: int
    sub_industries: List[str]


# ============================================================================
# Helper Functions
# ============================================================================

def industry_to_response(industry: Industry) -> IndustryResponse:
    """Convert Industry dataclass to response model"""
    return IndustryResponse(
        name=industry.name,
        category=industry.category.value,
        sub_industries=industry.sub_industries,
        search_keywords=industry.search_keywords,
        enabled=industry.enabled,
        priority=industry.priority,
        description=industry.description
    )


def country_to_response(country: Country) -> CountryResponse:
    """Convert Country dataclass to response model"""
    return CountryResponse(
        name=country.name,
        code=country.code,
        region=country.region.value,
        languages=country.languages,
        tld=country.tld,
        enabled=country.enabled,
        priority=country.priority,
        description=country.description
    )


# ============================================================================
# Industry Endpoints
# ============================================================================

@router.get("/industries", response_model=IndustryListResponse)
async def list_industries(
    category: Optional[str] = None,
    enabled_only: bool = True
):
    """
    List all industries available for company discovery.
    
    - **category**: Filter by industry category (technology, manufacturing, automotive, etc.)
    - **enabled_only**: Only return enabled industries (default: True)
    """
    if category:
        try:
            cat = IndustryCategory(category.lower())
            industries = get_industry_by_category(cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    else:
        industries = get_all_industries() if enabled_only else INDUSTRIES
    
    # Get unique categories
    categories = list(set(i.category.value for i in INDUSTRIES))
    
    return IndustryListResponse(
        industries=[industry_to_response(i) for i in industries],
        total=len(industries),
        categories=sorted(categories)
    )


@router.get("/industries/{industry_name}", response_model=IndustryResponse)
async def get_industry(industry_name: str):
    """
    Get details for a specific industry.
    Supports aliases (e.g., "IoT" resolves to "IoT (Internet of Things)").
    """
    # Try exact match first
    industry = get_industry_by_name(industry_name)
    
    # Try alias resolution
    if not industry:
        industry = resolve_industry_alias(industry_name)
    
    if not industry:
        raise HTTPException(status_code=404, detail=f"Industry not found: {industry_name}")
    
    return industry_to_response(industry)


@router.get("/industries/categories/list", response_model=List[str])
async def list_industry_categories():
    """List all available industry categories"""
    categories = list(set(i.category.value for i in INDUSTRIES))
    return sorted(categories)


@router.get("/sub-industries", response_model=List[str])
async def list_sub_industries():
    """List all sub-industries from all industries"""
    return get_all_sub_industries()


# ============================================================================
# Country Endpoints
# ============================================================================

@router.get("/countries", response_model=CountryListResponse)
async def list_countries(
    region: Optional[str] = None,
    enabled_only: bool = True
):
    """
    List all countries available for company discovery.
    
    - **region**: Filter by region (europe, north_america, asia, etc.)
    - **enabled_only**: Only return enabled countries (default: True)
    """
    if region:
        try:
            reg = Region(region.lower())
            countries = get_countries_by_region(reg)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid region: {region}")
    else:
        if enabled_only:
            countries = get_all_countries()
        else:
            countries = COUNTRIES
    
    # Get unique regions
    regions = list(set(c.region.value for c in COUNTRIES))
    
    return CountryListResponse(
        countries=[country_to_response(c) for c in countries],
        total=len(countries),
        regions=sorted(regions)
    )


@router.get("/countries/europe", response_model=CountryListResponse)
async def list_european_countries():
    """List all European countries (default focus)"""
    countries = get_european_countries()
    return CountryListResponse(
        countries=[country_to_response(c) for c in countries],
        total=len(countries),
        regions=["europe"]
    )


@router.get("/countries/{country_code}", response_model=CountryResponse)
async def get_country(country_code: str):
    """
    Get details for a specific country.
    Supports both ISO codes (DE, FR, NL) and names (Germany, France).
    """
    # Try code first
    country = get_country_by_code(country_code)
    
    # Try name
    if not country:
        country = get_country_by_name(country_code)
    
    # Try alias
    if not country:
        country = resolve_country_alias(country_code)
    
    if not country:
        raise HTTPException(status_code=404, detail=f"Country not found: {country_code}")
    
    return country_to_response(country)


@router.get("/countries/regions/list", response_model=List[str])
async def list_regions():
    """List all available regions"""
    regions = list(set(c.region.value for c in COUNTRIES))
    return sorted(regions)


# ============================================================================
# Discovery Status Endpoint
# ============================================================================

@router.get("/discovery/status", response_model=DiscoveryStatusResponse)
async def get_discovery_status():
    """
    Get current discovery configuration status.
    Shows which industries and countries are configured for scraping.
    """
    industries = get_all_industries()
    countries = get_european_countries()
    sub_industries = get_all_sub_industries()
    
    return DiscoveryStatusResponse(
        industries=[i.name for i in industries],
        countries=[c.code for c in countries],
        total_industries=len(industries),
        total_countries=len(countries),
        sub_industries=sub_industries
    )


# ============================================================================
# Search Query Generation (for debugging/testing)
# ============================================================================

@router.get("/discovery/test-queries")
async def test_discovery_queries(
    industry: str,
    country: str = "DE"
):
    """
    Generate sample search queries for an industry + country combination.
    Useful for testing discovery before running the scraper.
    """
    from app.scraper.discovery_rules import DiscoveryRules
    
    # Resolve industry
    ind = get_industry_by_name(industry)
    if not ind:
        ind = resolve_industry_alias(industry)
    if not ind:
        raise HTTPException(status_code=404, detail=f"Industry not found: {industry}")
    
    # Resolve country
    cty = get_country_by_code(country)
    if not cty:
        cty = get_country_by_name(country)
    if not cty:
        raise HTTPException(status_code=404, detail=f"Country not found: {country}")
    
    # Generate queries
    rules = DiscoveryRules()
    queries = rules.generate_queries(ind, cty)
    
    return {
        "industry": ind.name,
        "country": cty.name,
        "country_code": cty.code,
        "total_queries": len(queries),
        "queries": queries[:20],  # Limit to 20 for display
        "discovery_sources": [
            {"name": s.name, "type": s.source_type, "priority": s.priority}
            for s in rules.get_discovery_sources(ind, cty)
        ]
    }