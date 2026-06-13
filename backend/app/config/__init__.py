"""
Configuration Module
====================
Central configuration for industries and countries.
"""

from app.config.industries import (
    INDUSTRIES,
    Industry,
    IndustryCategory,
    get_all_industries,
    get_industry_by_name,
    get_industry_by_category,
    get_all_industry_names,
    get_all_sub_industries,
    get_search_queries_for_industry,
    resolve_industry_alias,
    INDUSTRY_ALIASES,
)

from app.config.countries import (
    COUNTRIES,
    Country,
    Region,
    get_all_countries,
    get_european_countries,
    get_country_by_code,
    get_country_by_name,
    get_countries_by_region,
    get_all_country_codes,
    get_all_country_names,
    get_country_tld,
    generate_search_queries,
    resolve_country_alias,
    COUNTRY_ALIASES,
)

__all__ = [
    # Industries
    "INDUSTRIES",
    "Industry",
    "IndustryCategory",
    "get_all_industries",
    "get_industry_by_name",
    "get_industry_by_category",
    "get_all_industry_names",
    "get_all_sub_industries",
    "get_search_queries_for_industry",
    "resolve_industry_alias",
    "INDUSTRY_ALIASES",
    
    # Countries
    "COUNTRIES",
    "Country",
    "Region",
    "get_all_countries",
    "get_european_countries",
    "get_country_by_code",
    "get_country_by_name",
    "get_countries_by_region",
    "get_all_country_codes",
    "get_all_country_names",
    "get_country_tld",
    "generate_search_queries",
    "resolve_country_alias",
    "COUNTRY_ALIASES",
]