from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, text, or_
from typing import List, Optional
from uuid import UUID
import numpy as np

from app.core.database import get_db
from app.core.config import settings
from app.models.models import (
    Company, Industry, SubIndustry, Domain, Technology,
    Product, Service, News, Document, Embedding
)
from app.schemas.schemas import SearchResponse, SearchResult

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, max_length=500),
    entity_type: Optional[str] = Query(None, description="Filter by entity type: company, product, service, news, document"),
    industry: Optional[str] = Query(None, description="Filter by industry name"),
    domain: Optional[str] = Query(None, description="Filter by domain name"),
    country: Optional[str] = Query(None, description="Filter by country"),
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    use_semantic: bool = Query(True, description="Use semantic search with embeddings"),
    db: Session = Depends(get_db)
):
    """
    Search across all entities using full-text search and optionally semantic search.
    """
    results = []
    
    if use_semantic:
        # For semantic search, we would typically call Ollama to get embeddings
        # and then do vector similarity search. For now, we fall back to full-text.
        pass
    
    # Full-text search on companies
    if entity_type is None or entity_type == "company":
        company_query = db.query(Company).options(
            joinedload(Company.industry_classifications)
        ).filter(
            or_(
                Company.name.ilike(f"%{q}%"),
                Company.description.ilike(f"%{q}%"),
                Company.short_description.ilike(f"%{q}%"),
                Company.business_summary.ilike(f"%{q}%"),
                Company.capabilities.ilike(f"%{q}%"),
                Company.expertise_areas.ilike(f"%{q}%")
            )
        )
        
        if industry:
            company_query = company_query.join(Company.industry_classifications).filter(
                Industry.name.ilike(f"%{industry}%")
            )
        
        if country:
            company_query = company_query.filter(Company.country.ilike(f"%{country}%"))
        
        if city:
            company_query = company_query.filter(Company.city.ilike(f"%{city}%"))
        
        companies = company_query.limit(limit).offset(offset).all()
        
        for company in companies:
            # Calculate a simple relevance score based on matches
            score = 0.0
            if q.lower() in company.name.lower():
                score += 0.5
            if company.description and q.lower() in company.description.lower():
                score += 0.3
            if company.business_summary and q.lower() in company.business_summary.lower():
                score += 0.2
            
            results.append(SearchResult(
                id=company.id,
                entity_type="company",
                name=company.name,
                description=company.short_description or company.description,
                score=score + 0.5,  # Base score for text match
                highlights=[company.name]
            ))
    
    # Full-text search on products
    if entity_type is None or entity_type == "product":
        product_query = db.query(Product).filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%"),
                Product.features.ilike(f"%{q}%"),
                Product.use_cases.ilike(f"%{q}%")
            )
        )
        products = product_query.limit(limit).offset(offset).all()
        
        for product in products:
            results.append(SearchResult(
                id=product.id,
                entity_type="product",
                name=product.name,
                description=product.description,
                score=0.6,
                highlights=[product.name]
            ))
    
    # Full-text search on services
    if entity_type is None or entity_type == "service":
        service_query = db.query(Service).filter(
            or_(
                Service.name.ilike(f"%{q}%"),
                Service.description.ilike(f"%{q}%")
            )
        )
        services = service_query.limit(limit).offset(offset).all()
        
        for service in services:
            results.append(SearchResult(
                id=service.id,
                entity_type="service",
                name=service.name,
                description=service.description,
                score=0.6,
                highlights=[service.name]
            ))
    
    # Full-text search on news
    if entity_type is None or entity_type == "news":
        news_query = db.query(News).filter(
            or_(
                News.title.ilike(f"%{q}%"),
                News.content.ilike(f"%{q}%")
            )
        ).order_by(desc(News.created_at)).limit(limit).offset(offset).all()
        
        for news in news_query:
            results.append(SearchResult(
                id=news.id,
                entity_type="news",
                name=news.title,
                description=news.content[:200] if news.content else None,
                score=0.5,
                highlights=[news.title]
            ))
    
    # Sort results by score
    results.sort(key=lambda x: x.score, reverse=True)
    
    return SearchResponse(
        results=results[:limit],
        total=len(results),
        query=q
    )


@router.get("/companies", response_model=List[SearchResult])
def search_companies(
    q: str = Query(..., min_length=1),
    industry: Optional[str] = None,
    domain: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    technology: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search specifically for companies with advanced filtering.
    """
    query = db.query(Company).options(
        joinedload(Company.industry_classifications),
        joinedload(Company.domain_classifications),
        joinedload(Company.technology_areas_list)
    )
    
    # Text search
    query = query.filter(
        or_(
            Company.name.ilike(f"%{q}%"),
            Company.description.ilike(f"%{q}%"),
            Company.short_description.ilike(f"%{q}%"),
            Company.business_summary.ilike(f"%{q}%"),
            Company.capabilities.ilike(f"%{q}%"),
            Company.core_competencies.ilike(f"%{q}%"),
            Company.expertise_areas.ilike(f"%{q}%")
        )
    )
    
    if industry:
        query = query.join(Company.industry_classifications).filter(
            Industry.name.ilike(f"%{industry}%")
        )
    
    if domain:
        query = query.join(Company.domain_classifications).filter(
            Domain.name.ilike(f"%{domain}%")
        )
    
    if technology:
        query = query.join(Company.technology_areas_list).filter(
            Technology.name.ilike(f"%{technology}%")
        )
    
    if country:
        query = query.filter(Company.country.ilike(f"%{country}%"))
    
    if city:
        query = query.filter(Company.city.ilike(f"%{city}%"))
    
    companies = query.limit(limit).all()
    
    results = []
    for company in companies:
        # Build description from various fields
        description_parts = []
        if company.short_description:
            description_parts.append(company.short_description)
        if company.business_summary:
            description_parts.append(company.business_summary)
        
        industries = [i.name for i in company.industry_classifications]
        domains = [d.name for d in company.domain_classifications]
        
        description = " | ".join(description_parts[:2]) if description_parts else None
        
        results.append(SearchResult(
            id=company.id,
            entity_type="company",
            name=company.name,
            description=description,
            score=1.0,
            highlights=[f"Industries: {', '.join(industries)}" if industries else None]
        ))
    
    return results


@router.get("/similar/{company_id}", response_model=List[SearchResult])
def find_similar_companies(
    company_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Find companies similar to the given company based on industries, domains, and capabilities.
    """
    company = db.query(Company).options(
        joinedload(Company.industry_classifications),
        joinedload(Company.domain_classifications),
        joinedload(Company.technology_areas_list)
    ).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company identifiers
    industry_ids = [i.id for i in company.industry_classifications]
    domain_ids = [d.id for d in company.domain_classifications]
    technology_ids = [t.id for t in company.technology_areas_list]
    
    # Find similar companies
    query = db.query(Company).options(
        joinedload(Company.industry_classifications)
    ).filter(Company.id != company_id)
    
    # Join with related tables
    from app.models.models import company_industries, company_domains, company_technologies
    
    similar_query = db.query(
        Company,
        func.count(company_industries.c.industry_id).label('industry_match'),
        func.count(company_domains.c.domain_id).label('domain_match'),
        func.count(company_technologies.c.technology_id).label('tech_match')
    ).outerjoin(
        company_industries,
        (Company.id == company_industries.c.company_id) & 
        (company_industries.c.industry_id.in_(industry_ids))
    ).outerjoin(
        company_domains,
        (Company.id == company_domains.c.company_id) & 
        (company_domains.c.domain_id.in_(domain_ids))
    ).outerjoin(
        company_technologies,
        (Company.id == company_technologies.c.company_id) & 
        (company_technologies.c.technology_id.in_(technology_ids))
    ).filter(Company.id != company_id).group_by(Company.id).order_by(
        desc('industry_match'),
        desc('domain_match'),
        desc('tech_match')
    ).limit(limit)
    
    results = []
    for row in similar_query.all():
        company_obj = row[0]
        industry_match = row[1]
        domain_match = row[2]
        tech_match = row[3]
        
        total_match = industry_match + domain_match + tech_match
        score = min(total_match / 5.0, 1.0)  # Normalize to 0-1
        
        industries = [i.name for i in company_obj.industry_classifications]
        
        results.append(SearchResult(
            id=company_obj.id,
            entity_type="company",
            name=company_obj.name,
            description=company_obj.short_description,
            score=score,
            highlights=[
                f"Industry matches: {industry_match}",
                f"Domain matches: {domain_match}",
                f"Technology matches: {tech_match}",
                f"Industries: {', '.join(industries)}" if industries else None
            ]
        ))
    
    return results


@router.get("/industries", response_model=List[SearchResult])
def search_industries(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search for industries.
    """
    industries = db.query(Industry).filter(
        or_(
            Industry.name.ilike(f"%{q}%"),
            Industry.description.ilike(f"%{q}%")
        )
    ).limit(limit).all()
    
    return [
        SearchResult(
            id=industry.id,
            entity_type="industry",
            name=industry.name,
            description=industry.description,
            score=1.0 if q.lower() in industry.name.lower() else 0.5,
            highlights=[industry.name]
        )
        for industry in industries
    ]


@router.get("/domains", response_model=List[SearchResult])
def search_domains(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search for domains.
    """
    domains = db.query(Domain).filter(
        or_(
            Domain.name.ilike(f"%{q}%"),
            Domain.description.ilike(f"%{q}%")
        )
    ).limit(limit).all()
    
    return [
        SearchResult(
            id=domain.id,
            entity_type="domain",
            name=domain.name,
            description=domain.description,
            score=1.0 if q.lower() in domain.name.lower() else 0.5,
            highlights=[domain.name]
        )
        for domain in domains
    ]


@router.get("/technologies", response_model=List[SearchResult])
def search_technologies(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search for technologies.
    """
    technologies = db.query(Technology).filter(
        or_(
            Technology.name.ilike(f"%{q}%"),
            Technology.description.ilike(f"%{q}%")
        )
    ).limit(limit).all()
    
    return [
        SearchResult(
            id=tech.id,
            entity_type="technology",
            name=tech.name,
            description=tech.description,
            score=1.0 if q.lower() in tech.name.lower() else 0.5,
            highlights=[tech.name]
        )
        for tech in technologies
    ]