from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional
from uuid import UUID
import math

from app.core.database import get_db
from app.models.models import (
    Company, Industry, SubIndustry, Domain, EngineeringDiscipline, Technology,
    Product, Service, Leadership, Location, News, Document,
    Snapshot, Change, ChatMessage
)
from app.schemas.schemas import (
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanyStatus,
    ProductCreate, ProductUpdate, ProductResponse,
    ServiceCreate, ServiceUpdate, ServiceResponse,
    LeadershipCreate, LeadershipUpdate, LeadershipResponse,
    LocationCreate, LocationUpdate, LocationResponse,
    NewsCreate, NewsResponse,
    DocumentCreate, DocumentResponse,
    PaginatedResponse
)

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=PaginatedResponse)
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[CompanyStatus] = None,
    is_monitored: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Company)
    
    if search:
        query = query.filter(
            or_(
                Company.name.ilike(f"%{search}%"),
                Company.description.ilike(f"%{search}%"),
                Company.short_description.ilike(f"%{search}%")
            )
        )
    
    if industry:
        query = query.join(Company.industry_classifications).filter(
            Industry.name.ilike(f"%{industry}%")
        )
    
    if country:
        query = query.filter(Company.country.ilike(f"%{country}%"))
    
    if city:
        query = query.filter(Company.city.ilike(f"%{city}%"))
    
    if status:
        query = query.filter(Company.status == status)
    
    if is_monitored is not None:
        query = query.filter(Company.is_monitored == is_monitored)
    
    total = query.count()
    
    offset = (page - 1) * page_size
    companies = query.options(
        joinedload(Company.industry_classifications),
        joinedload(Company.products),
        joinedload(Company.services)
    ).order_by(desc(Company.updated_at)).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=[CompanyResponse.model_validate(c) for c in companies],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: UUID, db: Session = Depends(get_db)):
    company = db.query(Company).options(
        joinedload(Company.industry_classifications),
        joinedload(Company.sub_industry_classifications),
        joinedload(Company.domain_classifications),
        joinedload(Company.products),
        joinedload(Company.services),
        joinedload(Company.leadership),
        joinedload(Company.locations),
        joinedload(Company.news),
        joinedload(Company.documents)
    ).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: UUID, company: CompanyUpdate, db: Session = Depends(get_db)):
    db_company = db.query(Company).filter(Company.id == company_id).first()
    
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = company.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_company, key, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: UUID, db: Session = Depends(get_db)):
    db_company = db.query(Company).filter(Company.id == company_id).first()
    
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db.delete(db_company)
    db.commit()
    return None


# Products
@router.get("/{company_id}/products", response_model=List[ProductResponse])
def list_company_products(company_id: UUID, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.company_id == company_id).all()
    return products


@router.post("/{company_id}/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_company_product(company_id: UUID, product: ProductCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_product = Product(company_id=company_id, **product.model_dump(exclude={'company_id'}))
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{company_id}/products/{product_id}", response_model=ProductResponse)
def update_company_product(company_id: UUID, product_id: UUID, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == company_id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{company_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_product(company_id: UUID, product_id: UUID, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == company_id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return None


# Services
@router.get("/{company_id}/services", response_model=List[ServiceResponse])
def list_company_services(company_id: UUID, db: Session = Depends(get_db)):
    services = db.query(Service).filter(Service.company_id == company_id).all()
    return services


@router.post("/{company_id}/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_company_service(company_id: UUID, service: ServiceCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_service = Service(company_id=company_id, **service.model_dump(exclude={'company_id'}))
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


# Leadership
@router.get("/{company_id}/leadership", response_model=List[LeadershipResponse])
def list_company_leadership(company_id: UUID, db: Session = Depends(get_db)):
    leadership = db.query(Leadership).filter(Leadership.company_id == company_id).all()
    return leadership


@router.post("/{company_id}/leadership", response_model=LeadershipResponse, status_code=status.HTTP_201_CREATED)
def create_company_leadership(company_id: UUID, leader: LeadershipCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_leader = Leadership(company_id=company_id, **leader.model_dump(exclude={'company_id'}))
    db.add(db_leader)
    db.commit()
    db.refresh(db_leader)
    return db_leader


# Locations
@router.get("/{company_id}/locations", response_model=List[LocationResponse])
def list_company_locations(company_id: UUID, db: Session = Depends(get_db)):
    locations = db.query(Location).filter(Location.company_id == company_id).all()
    return locations


@router.post("/{company_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_company_location(company_id: UUID, location: LocationCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_location = Location(company_id=company_id, **location.model_dump(exclude={'company_id'}))
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


# News
@router.get("/{company_id}/news", response_model=List[NewsResponse])
def list_company_news(company_id: UUID, db: Session = Depends(get_db)):
    news = db.query(News).filter(News.company_id == company_id).order_by(desc(News.published_date)).all()
    return news


@router.post("/{company_id}/news", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
def create_company_news(company_id: UUID, news_item: NewsCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_news = News(company_id=company_id, **news_item.model_dump(exclude={'company_id'}))
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news


# Documents
@router.get("/{company_id}/documents", response_model=List[DocumentResponse])
def list_company_documents(company_id: UUID, db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.company_id == company_id).all()
    return documents


@router.post("/{company_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_company_document(company_id: UUID, document: DocumentCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_document = Document(company_id=company_id, **document.model_dump(exclude={'company_id'}))
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


# Snapshots
@router.get("/{company_id}/snapshots")
def list_company_snapshots(company_id: UUID, db: Session = Depends(get_db)):
    snapshots = db.query(Snapshot).filter(Snapshot.company_id == company_id).order_by(desc(Snapshot.created_at)).all()
    return snapshots


@router.post("/{company_id}/snapshots", status_code=status.HTTP_201_CREATED)
def create_company_snapshot(company_id: UUID, db: Session = Depends(get_db)):
    company = db.query(Company).options(
        joinedload(Company.products),
        joinedload(Company.services),
        joinedload(Company.leadership),
        joinedload(Company.locations),
        joinedload(Company.customer_list),
        joinedload(Company.partner_list),
        joinedload(Company.news)
    ).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    snapshot_data = {
        "name": company.name,
        "description": company.description,
        "website": company.website,
        "headquarters": company.headquarters,
        "country": company.country,
        "city": company.city,
        "founded_year": company.founded_year,
        "employee_range": company.employee_range,
        "business_summary": company.business_summary,
        "business_model": company.business_model,
        "core_competencies": company.core_competencies,
        "capabilities": company.capabilities,
    }
    
    snapshot = Snapshot(
        company_id=company_id,
        snapshot_data=snapshot_data,
        products_snapshot=[{"name": p.name, "description": p.description} for p in company.products],
        services_snapshot=[{"name": s.name, "description": s.description} for s in company.services],
        leadership_snapshot=[{"name": l.name, "position": l.position} for l in company.leadership],
        locations_snapshot=[{"name": loc.name, "city": loc.city, "country": loc.country} for loc in company.locations],
        customers_snapshot=[{"name": c.name} for c in company.customer_list],
        partners_snapshot=[{"name": p.name} for p in company.partner_list],
        news_snapshot=[{"title": n.title, "published_date": str(n.published_date)} for n in company.news]
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


# Changes
@router.get("/{company_id}/changes")
def list_company_changes(
    company_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    changes = db.query(Change).filter(Change.company_id == company_id).order_by(desc(Change.detected_at)).limit(limit).all()
    return changes


# Chat History
@router.get("/{company_id}/chat")
def get_company_chat_history(
    company_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    messages = db.query(ChatMessage).filter(
        ChatMessage.company_id == company_id
    ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
    
    return list(reversed(messages))