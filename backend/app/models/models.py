from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, JSON, Index, Table, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class CompanyStatus(str, enum.Enum):
    ACTIVE = "active"
    MONITORING = "monitoring"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


# Association tables for many-to-many relationships
company_industries = Table(
    'company_industries',
    Base.metadata,
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('industry_id', UUID(as_uuid=True), ForeignKey('industries.id', ondelete='CASCADE'), primary_key=True)
)

company_sub_industries = Table(
    'company_sub_industries',
    Base.metadata,
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('sub_industry_id', UUID(as_uuid=True), ForeignKey('sub_industries.id', ondelete='CASCADE'), primary_key=True)
)

company_domains = Table(
    'company_domains',
    Base.metadata,
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('domain_id', UUID(as_uuid=True), ForeignKey('domains.id', ondelete='CASCADE'), primary_key=True)
)

company_engineering = Table(
    'company_engineering',
    Base.metadata,
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('engineering_id', UUID(as_uuid=True), ForeignKey('engineering_disciplines.id', ondelete='CASCADE'), primary_key=True)
)

company_technologies = Table(
    'company_technologies',
    Base.metadata,
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('technology_id', UUID(as_uuid=True), ForeignKey('technologies.id', ondelete='CASCADE'), primary_key=True)
)

company_markets = Table(
    'company_markets',
    Base.metadata,
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('market_id', UUID(as_uuid=True), ForeignKey('markets.id', ondelete='CASCADE'), primary_key=True)
)

company_customers = Table(
    'company_customers',
    Base.metadata,
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('customer_id', UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), primary_key=True)
)

company_partners = Table(
    'company_partners',
    Base.metadata,
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('partner_id', UUID(as_uuid=True), ForeignKey('partners.id', ondelete='CASCADE'), primary_key=True)
)


class Company(Base):
    __tablename__ = 'companies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False, index=True)
    legal_name = Column(String(500))
    brand_name = Column(String(500))
    website = Column(String(500))
    description = Column(Text)
    short_description = Column(String(1000))
    long_description = Column(Text)
    
    # Location
    headquarters = Column(String(500))
    country = Column(String(100), index=True)
    state = Column(String(100))
    city = Column(String(100), index=True)
    
    # Company Info
    founded_year = Column(Integer)
    employee_range = Column(String(50))
    company_size = Column(Integer)
    business_type = Column(String(100))
    
    # Status
    status = Column(SQLEnum(CompanyStatus), default=CompanyStatus.ACTIVE)
    is_monitored = Column(Boolean, default=False)
    
    # Business Intelligence
    business_summary = Column(Text)
    business_model = Column(Text)
    core_competencies = Column(ARRAY(String))
    expertise_areas = Column(ARRAY(String))
    capabilities = Column(ARRAY(String))
    use_cases = Column(ARRAY(String))
    solutions_offered = Column(ARRAY(String))
    business_problems_solved = Column(ARRAY(String))
    target_customers = Column(ARRAY(String))
    customer_segments = Column(ARRAY(String))
    industries_served = Column(ARRAY(String))
    markets_served = Column(ARRAY(String))
    regions_served = Column(ARRAY(String))
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True))
    
    # Relationships
    industry_classifications = relationship('Industry', secondary=company_industries, back_populates='companies')
    sub_industry_classifications = relationship('SubIndustry', secondary=company_sub_industries, back_populates='companies')
    domain_classifications = relationship('Domain', secondary=company_domains, back_populates='companies')
    engineering_disciplines_list = relationship('EngineeringDiscipline', secondary=company_engineering, back_populates='companies')
    technology_areas_list = relationship('Technology', secondary=company_technologies, back_populates='companies')
    market_list = relationship('Market', secondary=company_markets, back_populates='companies')
    customer_list = relationship('Customer', secondary=company_customers, back_populates='companies')
    partner_list = relationship('Partner', secondary=company_partners, back_populates='companies')
    
    products = relationship('Product', back_populates='company', cascade='all, delete-orphan')
    services = relationship('Service', back_populates='company', cascade='all, delete-orphan')
    leadership = relationship('Leadership', back_populates='company', cascade='all, delete-orphan')
    locations = relationship('Location', back_populates='company', cascade='all, delete-orphan')
    news = relationship('News', back_populates='company', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='company', cascade='all, delete-orphan')
    snapshots = relationship('Snapshot', back_populates='company', cascade='all, delete-orphan')
    changes = relationship('Change', back_populates='company', cascade='all, delete-orphan')
    chat_messages = relationship('ChatMessage', back_populates='company', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('ix_companies_name_search', 'name'),
        Index('ix_companies_website', 'website'),
    )


class Industry(Base):
    __tablename__ = 'industries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('industries.id', ondelete='SET NULL'))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    companies = relationship('Company', secondary=company_industries, back_populates='industry_classifications')
    sub_industries = relationship('SubIndustry', back_populates='parent_industry')
    
    __table_args__ = (
        Index('ix_industries_name', 'name'),
    )


class SubIndustry(Base):
    __tablename__ = 'sub_industries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    industry_id = Column(UUID(as_uuid=True), ForeignKey('industries.id', ondelete='CASCADE'))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    companies = relationship('Company', secondary=company_sub_industries, back_populates='sub_industry_classifications')
    parent_industry = relationship('Industry', back_populates='sub_industries')
    
    __table_args__ = (
        Index('ix_sub_industries_name', 'name'),
    )


class Domain(Base):
    __tablename__ = 'domains'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    companies = relationship('Company', secondary=company_domains, back_populates='domain_classifications')
    
    __table_args__ = (
        Index('ix_domains_name', 'name'),
    )


class EngineeringDiscipline(Base):
    __tablename__ = 'engineering_disciplines'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    companies = relationship('Company', secondary=company_engineering, back_populates='engineering_disciplines_list')
    
    __table_args__ = (
        Index('ix_engineering_name', 'name'),
    )


class Technology(Base):
    __tablename__ = 'technologies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    companies = relationship('Company', secondary=company_technologies, back_populates='technology_areas_list')
    
    __table_args__ = (
        Index('ix_technologies_name', 'name'),
    )


class Market(Base):
    __tablename__ = 'markets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    region = Column(String(100))
    country = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    companies = relationship('Company', secondary=company_markets, back_populates='market_list')
    
    __table_args__ = (
        Index('ix_markets_name', 'name'),
    )


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    industry = Column(String(200))
    case_study = Column(Text)
    reference = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    companies = relationship('Company', secondary=company_customers, back_populates='customer_list')
    
    __table_args__ = (
        Index('ix_customers_name', 'name'),
    )


class Partner(Base):
    __tablename__ = 'partners'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    partner_type = Column(String(100))  # strategic, technology, integration, channel
    description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    companies = relationship('Company', secondary=company_partners, back_populates='partner_list')
    
    __table_args__ = (
        Index('ix_partners_name', 'name'),
    )


class Product(Base):
    __tablename__ = 'products'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'))
    
    name = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(200))
    features = Column(ARRAY(String))
    benefits = Column(ARRAY(String))
    use_cases = Column(ARRAY(String))
    target_industry = Column(ARRAY(String))
    target_market = Column(ARRAY(String))
    
    metadata = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    company = relationship('Company', back_populates='products')
    
    __table_args__ = (
        Index('ix_products_name', 'name'),
        Index('ix_products_company', 'company_id'),
    )


class Service(Base):
    __tablename__ = 'services'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'))
    
    name = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(200))
    industries_served = Column(ARRAY(String))
    customer_segments = Column(ARRAY(String))
    
    metadata = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    company = relationship('Company', back_populates='services')
    
    __table_args__ = (
        Index('ix_services_name', 'name'),
        Index('ix_services_company', 'company_id'),
    )


class Leadership(Base):
    __tablename__ = 'leadership'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'))
    
    name = Column(String(300), nullable=False)
    position = Column(String(200))
    department = Column(String(200))
    biography = Column(Text)
    linkedin_url = Column(String(500))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    company = relationship('Company', back_populates='leadership')
    
    __table_args__ = (
        Index('ix_leadership_name', 'name'),
        Index('ix_leadership_company', 'company_id'),
    )


class Location(Base):
    __tablename__ = 'locations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'))
    
    location_type = Column(String(50))  # headquarters, office, factory, warehouse, service_center, manufacturing_plant
    name = Column(String(500))
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    latitude = Column(Float)
    longitude = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    company = relationship('Company', back_populates='locations')
    
    __table_args__ = (
        Index('ix_locations_company', 'company_id'),
        Index('ix_locations_country', 'country'),
    )


class News(Base):
    __tablename__ = 'news'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'))
    
    title = Column(String(1000), nullable=False)
    content = Column(Text)
    source = Column(String(500))
    source_url = Column(String(1000))
    news_type = Column(String(100))  # announcement, partnership, acquisition, expansion, product_launch, general
    published_date = Column(DateTime(timezone=True))
    
    metadata = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship('Company', back_populates='news')
    
    __table_args__ = (
        Index('ix_news_company', 'company_id'),
        Index('ix_news_published', 'published_date'),
    )


class Document(Base):
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'))
    
    title = Column(String(500), nullable=False)
    description = Column(Text)
    doc_type = Column(String(100))  # whitepaper, brochure, catalog, technical_doc, annual_report, pdf
    file_path = Column(String(1000))
    file_url = Column(String(1000))
    content = Column(Text)
    extracted_text = Column(Text)
    
    metadata = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    company = relationship('Company', back_populates='documents')
    
    __table_args__ = (
        Index('ix_documents_company', 'company_id'),
        Index('ix_documents_type', 'doc_type'),
    )


class Snapshot(Base):
    __tablename__ = 'snapshots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'))
    
    snapshot_data = Column(JSONB, nullable=False)
    products_snapshot = Column(JSONB)
    services_snapshot = Column(JSONB)
    leadership_snapshot = Column(JSONB)
    locations_snapshot = Column(JSONB)
    customers_snapshot = Column(JSONB)
    partners_snapshot = Column(JSONB)
    news_snapshot = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship('Company', back_populates='snapshots')
    
    __table_args__ = (
        Index('ix_snapshots_company', 'company_id'),
        Index('ix_snapshots_created', 'created_at'),
    )


class Change(Base):
    __tablename__ = 'changes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'))
    
    change_type = Column(String(100), nullable=False)  # new_product, removed_product, new_service, etc.
    description = Column(Text)
    previous_value = Column(JSONB)
    new_value = Column(JSONB)
    severity = Column(String(50))  # low, medium, high, critical
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship('Company', back_populates='changes')
    
    __table_args__ = (
        Index('ix_changes_company', 'company_id'),
        Index('ix_changes_detected', 'detected_at'),
        Index('ix_changes_type', 'change_type'),
    )


class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=True)
    
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    context = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship('Company', back_populates='chat_messages')
    
    __table_args__ = (
        Index('ix_chat_company', 'company_id'),
        Index('ix_chat_created', 'created_at'),
    )


class Embedding(Base):
    __tablename__ = 'embeddings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    entity_type = Column(String(50), nullable=False)  # company, product, service, document, news
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    content = Column(Text)
    embedding = Column(ARRAY(Float))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_embeddings_entity', 'entity_type', 'entity_id'),
    )


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(500), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(500), nullable=False)
    full_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())