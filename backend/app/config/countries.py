"""
Country Configuration
=====================
Defines countries and regions for company discovery.
This is the ONLY place where countries are defined - no hardcoding elsewhere.

Usage:
    from app.config.countries import COUNTRIES, get_european_countries, get_country_by_code
    
    # Get all European countries
    for country in get_european_countries():
        print(f"{country.name} ({country.code})")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Region(str, Enum):
    """Geographic regions"""
    EUROPE = "europe"
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"
    ASIA = "asia"
    AFRICA = "africa"
    OCEANIA = "oceania"
    MIDDLE_EAST = "middle_east"


@dataclass
class Country:
    """
    Represents a country with metadata for company discovery.
    """
    name: str
    code: str  # ISO 3166-1 alpha-2 code
    region: Region
    
    # Language codes (primary first)
    languages: List[str] = field(default_factory=lambda: ["en"])
    
    # TLD (Top Level Domain)
    tld: str = ""
    
    # Alternative names for search queries
    search_names: List[str] = field(default_factory=list)
    
    # Whether this country is enabled for scraping
    enabled: bool = True
    
    # Priority for scraping (1-10, higher = more priority)
    priority: int = 5
    
    # Description
    description: str = ""


# ============================================================================
# MAIN COUNTRY DEFINITIONS - FOCUS ON EUROPE
# ============================================================================

COUNTRIES: List[Country] = [
    # ----- EUROPEAN UNION -----
    Country(
        name="Germany",
        code="DE",
        region=Region.EUROPE,
        languages=["de", "en"],
        tld="de",
        search_names=["Germany", "Deutsch", "Deutsche"],
        priority=10,
        description="Major industrial hub - IoT, Automotive, Manufacturing"
    ),
    
    Country(
        name="France",
        code="FR",
        region=Region.EUROPE,
        languages=["fr", "en"],
        tld="fr",
        search_names=["France", "Français", "Française"],
        priority=9,
        description="Strong in aerospace, automotive, and technology"
    ),
    
    Country(
        name="Netherlands",
        code="NL",
        region=Region.EUROPE,
        languages=["nl", "en"],
        tld="nl",
        search_names=["Netherlands", "Holland", "Dutch"],
        priority=8,
        description="Hub for technology and manufacturing"
    ),
    
    Country(
        name="Belgium",
        code="BE",
        region=Region.EUROPE,
        languages=["nl", "fr", "de", "en"],
        tld="be",
        search_names=["Belgium", "Belgian", "Belgique"],
        priority=7,
        description="Strong in biotech and technology"
    ),
    
    Country(
        name="Austria",
        code="AT",
        region=Region.EUROPE,
        languages=["de", "en"],
        tld="at",
        search_names=["Austria", "Österreich", "Austrian"],
        priority=7,
        description="Strong in automation and industrial technology"
    ),
    
    Country(
        name="Switzerland",
        code="CH",
        region=Region.EUROPE,
        languages=["de", "fr", "it", "en"],
        tld="ch",
        search_names=["Switzerland", "Swiss", "Schweiz", "Suisse"],
        priority=8,
        description="Hub for medtech, fintech, and precision engineering"
    ),
    
    Country(
        name="Sweden",
        code="SE",
        region=Region.EUROPE,
        languages=["sv", "en"],
        tld="se",
        search_names=["Sweden", "Swedish", "Sverige"],
        priority=8,
        description="Leader in industrial automation and IoT"
    ),
    
    Country(
        name="Denmark",
        code="DK",
        region=Region.EUROPE,
        languages=["da", "en"],
        tld="dk",
        search_names=["Denmark", "Danish", "Danmark"],
        priority=7,
        description="Strong in clean tech and robotics"
    ),
    
    Country(
        name="Norway",
        code="NO",
        region=Region.EUROPE,
        languages=["no", "en"],
        tld="no",
        search_names=["Norway", "Norwegian", "Norge"],
        priority=7,
        description="Leader in offshore technology and energy"
    ),
    
    Country(
        name="Finland",
        code="FI",
        region=Region.EUROPE,
        languages=["fi", "sv", "en"],
        tld="fi",
        search_names=["Finland", "Finnish", "Suomi"],
        priority=7,
        description="Strong in IoT, mobile tech, and gaming"
    ),
    
    Country(
        name="Italy",
        code="IT",
        region=Region.EUROPE,
        languages=["it", "en"],
        tld="it",
        search_names=["Italy", "Italian", "Italia"],
        priority=7,
        description="Strong in manufacturing and automation"
    ),
    
    Country(
        name="Spain",
        code="ES",
        region=Region.EUROPE,
        languages=["es", "en"],
        tld="es",
        search_names=["Spain", "Spanish", "España"],
        priority=6,
        description="Growing tech hub in Southern Europe"
    ),
    
    Country(
        name="Portugal",
        code="PT",
        region=Region.EUROPE,
        languages=["pt", "en"],
        tld="pt",
        search_names=["Portugal", "Portuguese"],
        priority=6,
        description="Emerging tech hub with strong engineering talent"
    ),
    
    Country(
        name="Poland",
        code="PL",
        region=Region.EUROPE,
        languages=["pl", "en"],
        tld="pl",
        search_names=["Poland", "Polish", "Polska"],
        priority=6,
        description="Growing hub for software and outsourcing"
    ),
    
    Country(
        name="Czech Republic",
        code="CZ",
        region=Region.EUROPE,
        languages=["cs", "en"],
        tld="cz",
        search_names=["Czech Republic", "Czech", "Czechia", "Česko"],
        priority=6,
        description="Strong in manufacturing and automotive"
    ),
    
    Country(
        name="Hungary",
        code="HU",
        region=Region.EUROPE,
        languages=["hu", "en"],
        tld="hu",
        search_names=["Hungary", "Hungarian", "Magyarország"],
        priority=5,
        description="Growing tech and manufacturing sector"
    ),
    
    Country(
        name="Romania",
        code="RO",
        region=Region.EUROPE,
        languages=["ro", "en"],
        tld="ro",
        search_names=["Romania", "Romanian", "România"],
        priority=5,
        description="Emerging software development hub"
    ),
    
    Country(
        name="Greece",
        code="GR",
        region=Region.EUROPE,
        languages=["el", "en"],
        tld="gr",
        search_names=["Greece", "Greek", "Ελλάδα"],
        priority=5,
        description="Growing technology sector"
    ),
    
    Country(
        name="Ireland",
        code="IE",
        region=Region.EUROPE,
        languages=["en", "ga"],
        tld="ie",
        search_names=["Ireland", "Irish"],
        priority=8,
        description="European HQ for many tech companies"
    ),
    
    Country(
        name="United Kingdom",
        code="GB",
        region=Region.EUROPE,
        languages=["en"],
        tld="uk",
        search_names=["UK", "United Kingdom", "Britain", "British", "England"],
        priority=9,
        description="Major tech hub with strong R&D"
    ),
    
    # ----- OTHER EUROPEAN COUNTRIES -----
    Country(
        name="Luxembourg",
        code="LU",
        region=Region.EUROPE,
        languages=["fr", "de", "en"],
        tld="lu",
        search_names=["Luxembourg", "Luxembourgish"],
        priority=6,
        description="Financial and tech hub"
    ),
    
    Country(
        name="Slovenia",
        code="SI",
        region=Region.EUROPE,
        languages=["sl", "en"],
        tld="si",
        search_names=["Slovenia", "Slovenian"],
        priority=5,
        description="Strong in manufacturing and automation"
    ),
    
    Country(
        name="Slovakia",
        code="SK",
        region=Region.EUROPE,
        languages=["sk", "en"],
        tld="sk",
        search_names=["Slovakia", "Slovak"],
        priority=5,
        description="Growing automotive and electronics sector"
    ),
    
    Country(
        name="Croatia",
        code="HR",
        region=Region.EUROPE,
        languages=["hr", "en"],
        tld="hr",
        search_names=["Croatia", "Croatian"],
        priority=5,
        description="Emerging tech scene"
    ),
    
    Country(
        name="Estonia",
        code="EE",
        region=Region.EUROPE,
        languages=["et", "en"],
        tld="ee",
        search_names=["Estonia", "Estonian"],
        priority=6,
        description="Digital society leader (e-Residency, e-Governance)"
    ),
    
    Country(
        name="Latvia",
        code="LV",
        region=Region.EUROPE,
        languages=["lv", "en"],
        tld="lv",
        search_names=["Latvia", "Latvian"],
        priority=5,
        description="Growing tech and logistics hub"
    ),
    
    Country(
        name="Lithuania",
        code="LT",
        region=Region.EUROPE,
        languages=["lt", "en"],
        tld="lt",
        search_names=["Lithuania", "Lithuanian"],
        priority=5,
        description="Emerging tech hub in Baltics"
    ),
    
    Country(
        name="Bulgaria",
        code="BG",
        region=Region.EUROPE,
        languages=["bg", "en"],
        tld="bg",
        search_names=["Bulgaria", "Bulgarian"],
        priority=5,
        description="Growing software development sector"
    ),
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_countries() -> List[Country]:
    """Get all enabled countries"""
    return [c for c in COUNTRIES if c.enabled]


def get_european_countries() -> List[Country]:
    """Get all European countries"""
    return [c for c in COUNTRIES if c.region == Region.EUROPE and c.enabled]


def get_country_by_code(code: str) -> Optional[Country]:
    """Get country by ISO code"""
    return next((c for c in COUNTRIES if c.code.upper() == code.upper()), None)


def get_country_by_name(name: str) -> Optional[Country]:
    """Get country by name (fuzzy match)"""
    name_lower = name.lower()
    for c in COUNTRIES:
        if (c.name.lower() == name_lower or 
            name_lower in c.search_names or 
            name_lower == c.code.lower()):
            return c
    return None


def get_countries_by_region(region: Region) -> List[Country]:
    """Get all countries in a region"""
    return [c for c in COUNTRIES if c.region == region and c.enabled]


def get_all_country_codes() -> List[str]:
    """Get list of all country codes"""
    return [c.code for c in COUNTRIES]


def get_all_country_names() -> List[str]:
    """Get list of all country names"""
    return [c.name for c in COUNTRIES]


def get_country_tld(country: Country) -> str:
    """Get the TLD for a country"""
    return country.tld or country.code.lower()


def generate_search_queries(country: Country, industry_keywords: List[str]) -> List[str]:
    """
    Generate search queries for a country + industry combination.
    """
    queries = []
    
    # Country variations for search
    country_names = [country.name] + country.search_names
    
    for keyword in industry_keywords:
        for cn in country_names[:3]:  # Limit country name variations
            queries.append(f"{keyword} {cn}")
            queries.append(f"{keyword} company {cn}")
            queries.append(f"{keyword} manufacturer {cn}")
    
    return queries


# ============================================================================
# COUNTRY LOOKUP TABLES
# ============================================================================

# Map common names to canonical country codes
COUNTRY_ALIASES: Dict[str, str] = {
    # Germany
    "germany": "DE",
    "deutschland": "DE",
    "german": "DE",
    
    # France
    "france": "FR",
    "français": "FR",
    "french": "FR",
    
    # Netherlands
    "netherlands": "NL",
    "holland": "NL",
    "dutch": "NL",
    
    # Belgium
    "belgium": "BE",
    "belgian": "BE",
    "belgique": "BE",
    
    # Austria
    "austria": "AT",
    "österreich": "AT",
    "austrian": "AT",
    
    # Switzerland
    "switzerland": "CH",
    "swiss": "CH",
    "schweiz": "CH",
    "suisse": "CH",
    
    # Sweden
    "sweden": "SE",
    "swedish": "SE",
    "sverige": "SE",
    
    # UK
    "uk": "GB",
    "united kingdom": "GB",
    "britain": "GB",
    "england": "GB",
    "british": "GB",
    
    # Italy
    "italy": "IT",
    "italian": "IT",
    "italia": "IT",
    
    # Spain
    "spain": "ES",
    "spanish": "ES",
    "españa": "ES",
    
    # Poland
    "poland": "PL",
    "polish": "PL",
    "polska": "PL",
    
    # And more...
}


def resolve_country_alias(alias: str) -> Optional[Country]:
    """Resolve a country alias to the canonical Country object"""
    code = COUNTRY_ALIASES.get(alias.lower(), alias)
    return get_country_by_code(code)