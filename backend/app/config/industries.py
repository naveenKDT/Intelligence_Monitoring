"""
Industry Configuration
======================
Defines all industries and sub-industries for company discovery.
This is the ONLY place where industries are defined - no hardcoding elsewhere.

Usage:
    from app.config.industries import INDUSTRIES, get_industry_by_name, get_all_industry_names
    
    # Get all industries
    for industry in INDUSTRIES:
        print(f"{industry.name}: {industry.sub_industries}")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class IndustryCategory(str, Enum):
    """High-level industry categories"""
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    AUTOMOTIVE = "automotive"
    HEALTHCARE = "healthcare"
    ENERGY = "energy"
    AEROSPACE = "aerospace"
    AGRICULTURE = "agriculture"
    FINANCE = "finance"
    RETAIL = "retail"
    TELECOMMUNICATIONS = "telecommunications"
    CONSTRUCTION = "construction"
    CHEMICALS = "chemicals"


@dataclass
class Industry:
    """
    Represents an industry with its sub-industries and search keywords.
    """
    name: str
    category: IndustryCategory
    sub_industries: List[str] = field(default_factory=list)
    
    # Keywords for search queries - variations for better discovery
    search_keywords: List[str] = field(default_factory=list)
    
    # Common company suffixes in this industry
    company_suffixes: List[str] = field(default_factory=lambda: [
        "GmbH", "AG", "SE", "BV", "Ltd", "Inc", "LLC", "Corp"
    ])
    
    # Whether this industry is enabled for scraping
    enabled: bool = True
    
    # Priority for scraping (1-10, higher = more priority)
    priority: int = 5
    
    # Description for the industry
    description: str = ""


# ============================================================================
# MAIN INDUSTRY DEFINITIONS
# ============================================================================

INDUSTRIES: List[Industry] = [
    # ----- TECHNOLOGY -----
    Industry(
        name="IoT (Internet of Things)",
        category=IndustryCategory.TECHNOLOGY,
        sub_industries=[
            "Industrial IoT",
            "Consumer IoT",
            "Smart Home",
            "Smart City",
            "IoT Sensors",
            "IoT Platforms",
            "Edge Computing",
            "M2M Communication",
        ],
        search_keywords=[
            "IoT", "Internet of Things", "connected devices", "smart sensors",
            "industrial IoT", "IIoT", "IoT platform", "M2M"
        ],
        description="Companies developing IoT solutions, sensors, platforms, and connected devices"
    ),
    
    Industry(
        name="Embedded Systems",
        category=IndustryCategory.TECHNOLOGY,
        sub_industries=[
            "Embedded Software",
            "Firmware Development",
            "RTOS",
            "Microcontrollers",
            "Embedded Hardware",
            "Industrial Embedded",
            "Automotive Embedded",
            "Medical Embedded",
        ],
        search_keywords=[
            "embedded systems", "embedded software", "firmware", "RTOS",
            "microcontroller", "ARM", "real-time systems", "embedded Linux"
        ],
        description="Companies developing embedded systems, firmware, and real-time solutions"
    ),
    
    Industry(
        name="Software Development",
        category=IndustryCategory.TECHNOLOGY,
        sub_industries=[
            "SaaS",
            "Enterprise Software",
            "Mobile Apps",
            "Web Development",
            "Cloud Computing",
            "DevOps",
            "Cybersecurity",
            "AI/ML Software",
        ],
        search_keywords=[
            "software", "SaaS", "enterprise software", "cloud software",
            "app development", "software company", "tech startup"
        ],
        description="Software development companies, SaaS providers, and tech companies"
    ),
    
    Industry(
        name="Semiconductors",
        category=IndustryCategory.TECHNOLOGY,
        sub_industries=[
            "Chip Design",
            "Semiconductor Manufacturing",
            "Fabless",
            "EDA Tools",
            "Semiconductor Equipment",
            "Power Semiconductors",
            "Memory",
            "Sensors",
        ],
        search_keywords=[
            "semiconductor", "chip", "microprocessor", "IC design", "fab",
            "TSMC", "chipmaker", "silicon"
        ],
        description="Semiconductor design and manufacturing companies"
    ),
    
    # ----- AUTOMOTIVE -----
    Industry(
        name="Automotive",
        category=IndustryCategory.AUTOMOTIVE,
        sub_industries=[
            "EV (Electric Vehicles)",
            "Autonomous Driving",
            "Automotive Electronics",
            "Automotive Software",
            "Tier 1 Suppliers",
            "OEMs",
            "Automotive Components",
            "Connected Cars",
        ],
        search_keywords=[
            "automotive", "car manufacturer", "vehicle", "automotive supplier",
            "OEM", "Tier 1", "automotive electronics", "EV", "electric vehicle"
        ],
        priority=7,
        description="Automotive manufacturers, suppliers, and EV companies"
    ),
    
    Industry(
        name="Automotive Electronics",
        category=IndustryCategory.AUTOMOTIVE,
        sub_industries=[
            "ECU",
            "ADAS",
            "Infotainment",
            "Power Electronics",
            "Vehicle Networking",
            "Sensor Systems",
            "Lighting",
        ],
        search_keywords=[
            "automotive electronics", "ECU", "ADAS", "advanced driver assistance",
            "infotainment", "car electronics", "automotive chip"
        ],
        description="Automotive electronic components and systems"
    ),
    
    # ----- MANUFACTURING -----
    Industry(
        name="Industrial Automation",
        category=IndustryCategory.MANUFACTURING,
        sub_industries=[
            "PLC",
            "SCADA",
            "Industrial Robots",
            "DCS",
            "HMI",
            "Motion Control",
            "Industrial IoT",
            "Smart Factory",
        ],
        search_keywords=[
            "industrial automation", "PLC", "SCADA", "industrial robot",
            "factory automation", "manufacturing automation", "Industry 4.0"
        ],
        priority=7,
        description="Industrial automation, robotics, and manufacturing technology"
    ),
    
    Industry(
        name="Robotics",
        category=IndustryCategory.MANUFACTURING,
        sub_industries=[
            "Industrial Robots",
            "Collaborative Robots (Cobots)",
            "Service Robots",
            "AGV/AMR",
            "Robot Components",
            "Robot Software",
            "Medical Robots",
        ],
        search_keywords=[
            "robotics", "robot manufacturer", "industrial robot", "cobot",
            "collaborative robot", "AGV", "AMR", "automation robot"
        ],
        priority=7,
        description="Robotics companies, robot manufacturers, and automation"
    ),
    
    Industry(
        name="Machine Vision",
        category=IndustryCategory.MANUFACTURING,
        sub_industries=[
            "Industrial Vision",
            "Quality Control",
            "3D Vision",
            "Vision Sensors",
            "Smart Cameras",
            "OCR/Barcode",
        ],
        search_keywords=[
            "machine vision", "industrial vision", "vision system", "smart camera",
            "quality inspection", "computer vision", "image processing"
        ],
        description="Machine vision and industrial imaging companies"
    ),
    
    # ----- HEALTHCARE -----
    Industry(
        name="Medical Devices",
        category=IndustryCategory.HEALTHCARE,
        sub_industries=[
            "Diagnostic Equipment",
            "Therapeutic Devices",
            "Implantable Devices",
            "Surgical Robots",
            "Wearable Medical",
            "Medical Imaging",
            "IVD (In-Vitro Diagnostics)",
        ],
        search_keywords=[
            "medical device", "medical equipment", "healthcare technology",
            "diagnostic", "medical technology", "medtech"
        ],
        description="Medical device and healthcare technology companies"
    ),
    
    Industry(
        name="Digital Health",
        category=IndustryCategory.HEALTHCARE,
        sub_industries=[
            "Telemedicine",
            "Health Apps",
            "Wearable Health",
            "Health Data",
            "AI Healthcare",
            "Remote Monitoring",
        ],
        search_keywords=[
            "digital health", "healthtech", "telemedicine", "health app",
            "wearable health", "health monitoring", "eHealth"
        ],
        description="Digital health and healthtech companies"
    ),
    
    # ----- ENERGY -----
    Industry(
        name="Renewable Energy",
        category=IndustryCategory.ENERGY,
        sub_industries=[
            "Solar Energy",
            "Wind Energy",
            "Energy Storage",
            "Smart Grid",
            "Hydrogen",
            "Fuel Cells",
            "Power Electronics",
        ],
        search_keywords=[
            "renewable energy", "solar", "wind power", "energy storage",
            "clean energy", "sustainable energy", "green energy"
        ],
        description="Renewable energy and clean technology companies"
    ),
    
    Industry(
        name="Smart Grid",
        category=IndustryCategory.ENERGY,
        sub_industries=[
            "Grid Management",
            "Smart Meters",
            "Energy Storage",
            "Power Distribution",
            "Grid Automation",
        ],
        search_keywords=[
            "smart grid", "grid automation", "energy management",
            "smart meter", "power grid", "grid technology"
        ],
        description="Smart grid and energy management companies"
    ),
    
    # ----- AEROSPACE -----
    Industry(
        name="Aerospace",
        category=IndustryCategory.AEROSPACE,
        sub_industries=[
            "Aircraft Manufacturing",
            "Space Technology",
            "Avionics",
            "Defense",
            "UAV/Drone",
            "Aircraft Components",
        ],
        search_keywords=[
            "aerospace", "aircraft", "aviation", "defense", "drone",
            "UAV", "space technology", "avionics"
        ],
        description="Aerospace, defense, and aviation companies"
    ),
    
    # ----- AGRICULTURE -----
    Industry(
        name="Agritech",
        category=IndustryCategory.AGRICULTURE,
        sub_industries=[
            "Precision Agriculture",
            "Smart Farming",
            "Agricultural Drones",
            "Vertical Farming",
            "Agri Sensors",
            "Farm Management",
            "Food Technology",
        ],
        search_keywords=[
            "agritech", "agricultural technology", "smart farming", "precision agriculture",
            "vertical farming", "agri drone", "farm technology"
        ],
        description="Agricultural technology and farming automation companies"
    ),
    
    # ----- TELECOMMUNICATIONS -----
    Industry(
        name="Telecommunications",
        category=IndustryCategory.TELECOMMUNICATIONS,
        sub_industries=[
            "5G",
            "Network Equipment",
            "Telecom Hardware",
            "Satellite Communications",
            "Network Software",
            "IoT Connectivity",
        ],
        search_keywords=[
            "telecommunications", "telecom", "network equipment", "5G",
            "wireless", "mobile network", "telecom hardware"
        ],
        description="Telecommunications equipment and network companies"
    ),
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_industries() -> List[Industry]:
    """Get all enabled industries"""
    return [ind for ind in INDUSTRIES if ind.enabled]


def get_industry_by_name(name: str) -> Optional[Industry]:
    """Get industry by exact name match"""
    return next((ind for ind in INDUSTRIES if ind.name.lower() == name.lower()), None)


def get_industry_by_category(category: IndustryCategory) -> List[Industry]:
    """Get all industries in a category"""
    return [ind for ind in INDUSTRIES if ind.category == category]


def get_all_industry_names() -> List[str]:
    """Get list of all industry names"""
    return [ind.name for ind in INDUSTRIES]


def get_all_sub_industries() -> List[str]:
    """Get all sub-industries from all industries"""
    subs = []
    for ind in INDUSTRIES:
        subs.extend(ind.sub_industries)
    return list(set(subs))


def get_search_queries_for_industry(industry: Industry, country) -> List[str]:
    """
    Generate search queries for an industry + country combination.
    This is the core function for dynamic URL discovery.
    """
    queries = []
    country_name = country.name if hasattr(country, 'name') else str(country)
    country_clean = country_name.strip()
    
    for keyword in industry.search_keywords:
        # Various query formats
        queries.append(f"{keyword} company {country_clean}")
        queries.append(f"{keyword} {country_clean}")
        queries.append(f"{keyword} manufacturer {country_clean}")
        queries.append(f"{keyword} solutions {country_clean}")
        queries.append(f"{keyword} technology {country_clean}")
        
        # For sub-industries
        for sub in industry.sub_industries[:3]:  # Limit to avoid too many queries
            queries.append(f"{sub} {country_clean}")
    
    return queries


# ============================================================================
# INDUSTRY LOOKUP TABLES
# ============================================================================

# Map common names to canonical industry names
INDUSTRY_ALIASES: Dict[str, str] = {
    "iot": "IoT (Internet of Things)",
    "internet of things": "IoT (Internet of Things)",
    "embedded": "Embedded Systems",
    "embedded systems": "Embedded Systems",
    "software": "Software Development",
    "software development": "Software Development",
    "automotive": "Automotive",
    "auto": "Automotive",
    "automation": "Industrial Automation",
    "industrial automation": "Industrial Automation",
    "robotics": "Robotics",
    "robots": "Robotics",
    "medical": "Medical Devices",
    "medical devices": "Medical Devices",
    "health": "Digital Health",
    "digital health": "Digital Health",
    "energy": "Renewable Energy",
    "renewable": "Renewable Energy",
    "aerospace": "Aerospace",
    "aviation": "Aerospace",
    "agri": "Agritech",
    "agriculture": "Agritech",
    "farming": "Agritech",
    "telecom": "Telecommunications",
    "telco": "Telecommunications",
    "semiconductor": "Semiconductors",
    "chip": "Semiconductors",
    "vision": "Machine Vision",
    "machine vision": "Machine Vision",
}


def resolve_industry_alias(alias: str) -> Optional[Industry]:
    """Resolve an industry alias to the canonical Industry object"""
    canonical = INDUSTRY_ALIASES.get(alias.lower(), alias)
    return get_industry_by_name(canonical)