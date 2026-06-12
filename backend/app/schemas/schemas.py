from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums
class CompanyStatus(str, Enum):
    ACTIVE = "active"
    MONITORING = "monitoring"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ChangeSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Base Schemas
class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Company Schemas
class CompanyBase(BaseModel):
    name: str = Field(..., max_length=500)
    legal_name: Optional[str] = Field(None, max_length=500)
    brand_name: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=1000)
    long_description: Optional[str] = None
    headquarters: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = None
    employee_range: Optional[str] = Field(None, max_length=50)
    company_size: Optional[int] = None
    business_type: Optional[str] = Field(None, max_length=100)
    business_summary: Optional[str] = None
    business_model: Optional[str] = None
    core_competencies: Optional[List[str]] = []
    expertise_areas: Optional[List[str]] = []
    capabilities: Optional[List[str]] = []
    use_cases: Optional[List[str]] = []
    solutions_offered: Optional[List[str]] = []
    business_problems_solved: Optional[List[str]] = []
    target_customers: Optional[List[str]] = []
    customer_segments: Optional[List[str]] = []
    industries_served: Optional[List[str]] = []
    markets_served: Optional[List[str]] = []
    regions_served: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    legal_name: Optional[str] = Field(None, max_length=500)
    brand_name: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=1000)
    long_description: Optional[str] = None
    headquarters: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = None
    employee_range: Optional[str] = Field(None, max_length=50)
    company_size: Optional[int] = None
    business_type: Optional[str] = Field(None, max_length=100)
    business_summary: Optional[str] = None
    business_model: Optional[str] = None
    core_competencies: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    solutions_offered: Optional[List[str]] = None
    business_problems_solved: Optional[List[str]] = None
    target_customers: Optional[List[str]] = None
    customer_segments: Optional[List[str]] = None
    industries_served: Optional[List[str]] = None
    markets_served: Optional[List[str]] = None
    regions_served: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[CompanyStatus] = None
    is_monitored: Optional[bool] = None


class CompanyResponse(CompanyBase, TimestampMixin):
    id: UUID
    status: CompanyStatus = CompanyStatus.ACTIVE
    is_monitored: bool = False
    last_scraped_at: Optional[datetime] = None
    industry_classifications: List["IndustryResponse"] = []
    sub_industry_classifications: List["SubIndustryResponse"] = []
    domain_classifications: List["DomainResponse"] = []
    products: List["ProductResponse"] = []
    services: List["ServiceResponse"] = []
    leadership: List["LeadershipResponse"] = []
    locations: List["LocationResponse"] = []
    
    class Config:
        from_attributes = True


# Industry Schemas
class IndustryBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class IndustryCreate(IndustryBase):
    pass


class IndustryResponse(IndustryBase, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True


class SubIndustryBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    industry_id: Optional[UUID] = None


class SubIndustryCreate(SubIndustryBase):
    pass


class SubIndustryResponse(SubIndustryBase, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True


class DomainBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class DomainCreate(DomainBase):
    pass


class DomainResponse(DomainBase, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True


# Engineering Schemas
class EngineeringDisciplineBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class EngineeringDisciplineCreate(EngineeringDisciplineBase):
    pass


class EngineeringDisciplineResponse(EngineeringDisciplineBase, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True


# Technology Schemas
class TechnologyBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class TechnologyCreate(TechnologyBase):
    pass


class TechnologyResponse(TechnologyBase, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True


# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=200)
    features: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    use_cases: Optional[List[str]] = []
    target_industry: Optional[List[str]] = []
    target_market: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class ProductCreate(ProductBase):
    company_id: UUID


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=200)
    features: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    target_industry: Optional[List[str]] = None
    target_market: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProductResponse(ProductBase, TimestampMixin):
    id: UUID
    company_id: UUID
    
    class Config:
        from_attributes = True


# Service Schemas
class ServiceBase(BaseModel):
    name: str = Field(..., max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=200)
    industries_served: Optional[List[str]] = []
    customer_segments: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class ServiceCreate(ServiceBase):
    company_id: UUID


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=200)
    industries_served: Optional[List[str]] = None
    customer_segments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ServiceResponse(ServiceBase, TimestampMixin):
    id: UUID
    company_id: UUID
    
    class Config:
        from_attributes = True


# Leadership Schemas
class LeadershipBase(BaseModel):
    name: str = Field(..., max_length=300)
    position: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    biography: Optional[str] = None
    linkedin_url: Optional[str] = Field(None, max_length=500)


class LeadershipCreate(LeadershipBase):
    company_id: UUID


class LeadershipUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=300)
    position: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    biography: Optional[str] = None
    linkedin_url: Optional[str] = Field(None, max_length=500)


class LeadershipResponse(LeadershipBase, TimestampMixin):
    id: UUID
    company_id: UUID
    
    class Config:
        from_attributes = True


# Location Schemas
class LocationBase(BaseModel):
    location_type: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationCreate(LocationBase):
    company_id: UUID


class LocationUpdate(BaseModel):
    location_type: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationResponse(LocationBase, TimestampMixin):
    id: UUID
    company_id: UUID
    
    class Config:
        from_attributes = True


# News Schemas
class NewsBase(BaseModel):
    title: str = Field(..., max_length=1000)
    content: Optional[str] = None
    source: Optional[str] = Field(None, max_length=500)
    source_url: Optional[str] = Field(None, max_length=1000)
    news_type: Optional[str] = Field(None, max_length=100)
    published_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}


class NewsCreate(NewsBase):
    company_id: UUID


class NewsResponse(NewsBase, TimestampMixin):
    id: UUID
    company_id: UUID
    
    class Config:
        from_attributes = True


# Document Schemas
class DocumentBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    doc_type: Optional[str] = Field(None, max_length=100)
    file_path: Optional[str] = Field(None, max_length=1000)
    file_url: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = None
    extracted_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class DocumentCreate(DocumentBase):
    company_id: UUID


class DocumentResponse(DocumentBase, TimestampMixin):
    id: UUID
    company_id: UUID
    
    class Config:
        from_attributes = True


# Snapshot Schemas
class SnapshotBase(BaseModel):
    snapshot_data: Dict[str, Any]
    products_snapshot: Optional[Dict[str, Any]] = None
    services_snapshot: Optional[Dict[str, Any]] = None
    leadership_snapshot: Optional[Dict[str, Any]] = None
    locations_snapshot: Optional[Dict[str, Any]] = None
    customers_snapshot: Optional[Dict[str, Any]] = None
    partners_snapshot: Optional[Dict[str, Any]] = None
    news_snapshot: Optional[Dict[str, Any]] = None


class SnapshotCreate(SnapshotBase):
    company_id: UUID


class SnapshotResponse(SnapshotBase, TimestampMixin):
    id: UUID
    company_id: UUID
    
    class Config:
        from_attributes = True


# Change Schemas
class ChangeBase(BaseModel):
    change_type: str = Field(..., max_length=100)
    description: Optional[str] = None
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    severity: Optional[ChangeSeverity] = ChangeSeverity.LOW


class ChangeCreate(ChangeBase):
    company_id: UUID


class ChangeResponse(ChangeBase, TimestampMixin):
    id: UUID
    company_id: UUID
    detected_at: datetime
    
    class Config:
        from_attributes = True


# Chat Schemas
class ChatMessageBase(BaseModel):
    content: str
    company_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None


class ChatMessageCreate(ChatMessageBase):
    role: str = "user"


class ChatMessageResponse(ChatMessageBase, TimestampMixin):
    id: UUID
    role: str
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    company_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: UUID


# Search Schemas
class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = {}
    limit: int = Field(default=20, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResult(BaseModel):
    id: UUID
    entity_type: str
    name: str
    description: Optional[str] = None
    score: float
    highlights: Optional[List[str]] = []


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str


# Intelligence Schemas
class IntelligenceExtractRequest(BaseModel):
    content: str
    content_type: str = "website"  # website, document, news
    company_id: Optional[UUID] = None


class IntelligenceExtractResponse(BaseModel):
    company_data: Dict[str, Any]
    products: List[Dict[str, Any]]
    services: List[Dict[str, Any]]
    technologies: List[str]
    industries: List[str]
    domains: List[str]


class ClassificationRequest(BaseModel):
    company_id: UUID
    classification_type: str  # industry, domain, technology


class ClassificationResponse(BaseModel):
    classifications: List[Dict[str, Any]]
    confidence: float


# Dashboard Schemas
class ExecutiveDashboard(BaseModel):
    total_companies: int
    total_industries: int
    total_domains: int
    total_products: int
    total_services: int
    total_customers: int
    total_partners: int
    active_monitoring: int
    recent_changes: int
    growth_signals: int
    companies_by_industry: List[Dict[str, Any]]
    companies_by_country: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


class IndustryDashboard(BaseModel):
    companies_by_industry: List[Dict[str, Any]]
    companies_by_domain: List[Dict[str, Any]]
    industry_trends: List[Dict[str, Any]]
    technology_trends: List[Dict[str, Any]]
    growth_trends: List[Dict[str, Any]]
    hiring_trends: List[Dict[str, Any]]


class CompanyDashboard(BaseModel):
    company: CompanyResponse
    products_count: int
    services_count: int
    customers_count: int
    partners_count: int
    locations_count: int
    news_count: int
    documents_count: int
    changes_count: int
    ai_insights: Dict[str, Any]
    change_timeline: List[ChangeResponse]


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    id: UUID
    is_active: bool
    is_superuser: bool
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


# Pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Update forward references
CompanyResponse.model_rebuild()