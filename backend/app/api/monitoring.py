from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import json

from app.core.database import get_db
from app.core.config import settings
from app.models.models import (
    Company, Industry, Domain, Technology, Product, Service,
    Leadership, Location, Customer, Partner, News, Document,
    Snapshot, Change, ScrapeQueue, ScrapeStatus
)
from app.schemas.schemas import (
    CompanyResponse, ChangeResponse, ChangeSeverity,
    ExecutiveDashboard, IndustryDashboard, CompanyDashboard,
    SnapshotCreate, SnapshotResponse
)
from app.workers.tasks import scrape_company_task, check_for_changes_task

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/scrape-queue/stats")
def get_scrape_queue_stats(db: Session = Depends(get_db)):
    """
    Get statistics about the scrape queue.
    """
    total = db.query(ScrapeQueue).count()
    pending = db.query(ScrapeQueue).filter(ScrapeQueue.status == ScrapeStatus.PENDING).count()
    scraping = db.query(ScrapeQueue).filter(ScrapeQueue.status == ScrapeStatus.SCRAPING).count()
    completed = db.query(ScrapeQueue).filter(ScrapeQueue.status == ScrapeStatus.COMPLETED).count()
    failed = db.query(ScrapeQueue).filter(ScrapeQueue.status == ScrapeStatus.FAILED).count()
    queued = db.query(ScrapeQueue).filter(ScrapeQueue.status == ScrapeStatus.QUEUED).count()
    
    return {
        "total": total,
        "pending": pending,
        "scraping": scraping,
        "completed": completed,
        "failed": failed,
        "queued": queued,
        "ready_to_scrape": pending + queued
    }


@router.get("/scrape-queue")
def get_scrape_queue(
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get items in the scrape queue.
    """
    query = db.query(ScrapeQueue)
    
    if status:
        try:
            status_enum = ScrapeStatus(status)
            query = query.filter(ScrapeQueue.status == status_enum)
        except ValueError:
            pass
    
    items = query.order_by(
        ScrapeQueue.priority.desc(),
        ScrapeQueue.created_at.asc()
    ).limit(limit).all()
    
    return [
        {
            "id": str(item.id),
            "url": item.url,
            "source": item.source,
            "status": item.status.value if item.status else None,
            "priority": item.priority,
            "retry_count": item.retry_count,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "started_at": item.started_at.isoformat() if item.started_at else None,
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            "error_message": item.error_message,
        }
        for item in items
    ]


@router.post("/scrape-queue/add")
def add_to_scrape_queue(
    url: str,
    priority: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Add a URL to the scrape queue.
    """
    # Check if already exists
    existing = db.query(ScrapeQueue).filter(ScrapeQueue.url == url).first()
    if existing:
        return {"message": "URL already in queue", "id": str(existing.id), "status": existing.status.value}
    
    queue_item = ScrapeQueue(
        url=url,
        source="manual",
        status=ScrapeStatus.PENDING,
        priority=priority
    )
    db.add(queue_item)
    db.commit()
    db.refresh(queue_item)
    
    return {"message": "Added to queue", "id": str(queue_item.id)}


@router.delete("/scrape-queue/{item_id}")
def remove_from_scrape_queue(item_id: UUID, db: Session = Depends(get_db)):
    """
    Remove an item from the scrape queue.
    """
    item = db.query(ScrapeQueue).filter(ScrapeQueue.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    db.delete(item)
    db.commit()
    
    return {"message": "Removed from queue"}


@router.post("/scrape-queue/clear-failed")
def clear_failed_items(db: Session = Depends(get_db)):
    """
    Clear all failed items from the queue.
    """
    deleted = db.query(ScrapeQueue).filter(ScrapeQueue.status == ScrapeStatus.FAILED).delete()
    db.commit()
    
    return {"message": f"Cleared {deleted} failed items"}


@router.get("/companies", response_model=List[CompanyResponse])
def get_monitored_companies(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get list of companies currently being monitored.
    """
    companies = db.query(Company).options(
        joinedload(Company.industry_classifications),
        joinedload(Company.products),
        joinedload(Company.services)
    ).filter(
        Company.is_monitored == True
    ).order_by(desc(Company.last_scraped_at)).limit(limit).all()
    
    return companies


@router.post("/companies/{company_id}/enable")
def enable_monitoring(company_id: UUID, db: Session = Depends(get_db)):
    """
    Enable monitoring for a company.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.is_monitored = True
    company.status = "monitoring"
    db.commit()
    
    return {"message": "Monitoring enabled", "company_id": str(company_id)}


@router.post("/companies/{company_id}/disable")
def disable_monitoring(company_id: UUID, db: Session = Depends(get_db)):
    """
    Disable monitoring for a company.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.is_monitored = False
    company.status = "active"
    db.commit()
    
    return {"message": "Monitoring disabled", "company_id": str(company_id)}


@router.post("/scrape")
def trigger_scrape(
    company_id: Optional[UUID] = None,
    url: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Trigger a scrape job for a company or URL.
    """
    if company_id:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        scrape_url = company.website
    elif url:
        scrape_url = url
    else:
        raise HTTPException(status_code=400, detail="Either company_id or url must be provided")
    
    # Queue the scrape task
    task = scrape_company_task.delay(scrape_url, str(company_id) if company_id else None)
    
    return {
        "message": "Scrape job queued",
        "task_id": task.id,
        "url": scrape_url
    }


@router.get("/changes", response_model=List[ChangeResponse])
def get_changes(
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = None,
    change_type: Optional[str] = None,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get detected changes across all monitored companies.
    """
    query = db.query(Change).options(
        joinedload(Change.company)
    ).filter(
        Change.detected_at >= datetime.utcnow() - timedelta(days=days)
    )
    
    if severity:
        query = query.filter(Change.severity == severity)
    
    if change_type:
        query = query.filter(Change.change_type == change_type)
    
    changes = query.order_by(desc(Change.detected_at)).limit(limit).all()
    
    return changes


@router.get("/changes/company/{company_id}", response_model=List[ChangeResponse])
def get_company_changes(
    company_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get changes for a specific company.
    """
    changes = db.query(Change).filter(
        Change.company_id == company_id
    ).order_by(desc(Change.detected_at)).limit(limit).all()
    
    return changes


@router.post("/check-changes/{company_id}")
def check_company_changes(
    company_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger change detection for a company.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    task = check_for_changes_task.delay(str(company_id))
    
    return {
        "message": "Change detection job queued",
        "task_id": task.id,
        "company_id": str(company_id)
    }


# Dashboard API
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("/executive", response_model=ExecutiveDashboard)
def get_executive_dashboard(db: Session = Depends(get_db)):
    """
    Get executive dashboard metrics.
    """
    # Basic counts
    total_companies = db.query(Company).count()
    total_industries = db.query(Industry).count()
    total_domains = db.query(Domain).count()
    total_products = db.query(Product).count()
    total_services = db.query(Service).count()
    total_customers = db.query(Customer).count()
    total_partners = db.query(Partner).count()
    
    # Active monitoring
    active_monitoring = db.query(Company).filter(Company.is_monitored == True).count()
    
    # Recent changes (last 7 days)
    recent_changes = db.query(Change).filter(
        Change.detected_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    # Growth signals (new companies in last 30 days)
    growth_signals = db.query(Company).filter(
        Company.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Companies by industry
    industry_counts = db.query(
        Industry.name,
        func.count(Company.id).label('count')
    ).join(Company.industry_classifications).group_by(Industry.name).order_by(
        desc('count')
    ).limit(20).all()
    
    companies_by_industry = [
        {"name": name, "count": count}
        for name, count in industry_counts
    ]
    
    # Companies by country
    country_counts = db.query(
        Company.country,
        func.count(Company.id).label('count')
    ).filter(
        Company.country.isnot(None)
    ).group_by(Company.country).order_by(
        desc('count')
    ).limit(20).all()
    
    companies_by_country = [
        {"country": country, "count": count}
        for country, count in country_counts
    ]
    
    # Recent activity (recent changes with company names)
    recent_activity_query = db.query(
        Change, Company.name
    ).join(Change.company).order_by(
        desc(Change.detected_at)
    ).limit(10).all()
    
    recent_activity = [
        {
            "company_name": name,
            "change_type": change.change_type,
            "description": change.description,
            "detected_at": change.detected_at.isoformat() if change.detected_at else None,
            "severity": change.severity
        }
        for change, name in recent_activity_query
    ]
    
    return ExecutiveDashboard(
        total_companies=total_companies,
        total_industries=total_industries,
        total_domains=total_domains,
        total_products=total_products,
        total_services=total_services,
        total_customers=total_customers,
        total_partners=total_partners,
        active_monitoring=active_monitoring,
        recent_changes=recent_changes,
        growth_signals=growth_signals,
        companies_by_industry=companies_by_industry,
        companies_by_country=companies_by_country,
        recent_activity=recent_activity
    )


@dashboard_router.get("/industry", response_model=IndustryDashboard)
def get_industry_dashboard(db: Session = Depends(get_db)):
    """
    Get industry dashboard metrics.
    """
    # Companies by industry
    industry_counts = db.query(
        Industry.name,
        func.count(Company.id).label('count')
    ).join(Company.industry_classifications).group_by(Industry.name).order_by(
        desc('count')
    ).all()
    
    companies_by_industry = [
        {"name": name, "count": count}
        for name, count in industry_counts
    ]
    
    # Companies by domain
    domain_counts = db.query(
        Domain.name,
        func.count(Company.id).label('count')
    ).join(Company.domain_classifications).group_by(Domain.name).order_by(
        desc('count')
    ).all()
    
    companies_by_domain = [
        {"name": name, "count": count}
        for name, count in domain_counts
    ]
    
    # Industry trends (monthly company additions)
    industry_trends = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        count = db.query(Company).filter(
            Company.created_at >= month_start,
            Company.created_at < month_end
        ).count()
        
        industry_trends.append({
            "month": month_start.strftime("%Y-%m"),
            "companies_added": count
        })
    
    industry_trends.reverse()
    
    # Technology trends
    tech_counts = db.query(
        Technology.name,
        func.count(Company.id).label('count')
    ).join(Company.technology_areas_list).group_by(Technology.name).order_by(
        desc('count')
    ).limit(10).all()
    
    technology_trends = [
        {"name": name, "count": count}
        for name, count in tech_counts
    ]
    
    # Growth trends (monitored companies growth)
    growth_trends = []
    for i in range(6):
        day_start = datetime.utcnow() - timedelta(days=30 * i)
        
        total = db.query(Company).filter(
            Company.created_at <= day_start
        ).count()
        
        monitored = db.query(Company).filter(
            Company.created_at <= day_start,
            Company.is_monitored == True
        ).count()
        
        growth_trends.append({
            "period": day_start.strftime("%Y-%m-%d"),
            "total_companies": total,
            "monitored_companies": monitored
        })
    
    growth_trends.reverse()
    
    # Hiring trends (based on job postings or growth signals)
    hiring_trends = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        # Count companies with recent growth signals
        growing = db.query(Company).filter(
            Company.updated_at >= month_start,
            Company.updated_at < month_end
        ).count()
        
        hiring_trends.append({
            "month": month_start.strftime("%Y-%m"),
            "activity_score": growing
        })
    
    hiring_trends.reverse()
    
    return IndustryDashboard(
        companies_by_industry=companies_by_industry,
        companies_by_domain=companies_by_domain,
        industry_trends=industry_trends,
        technology_trends=technology_trends,
        growth_trends=growth_trends,
        hiring_trends=hiring_trends
    )


@dashboard_router.get("/company/{company_id}", response_model=CompanyDashboard)
def get_company_dashboard(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get detailed dashboard for a specific company.
    """
    company = db.query(Company).options(
        joinedload(Company.industry_classifications),
        joinedload(Company.sub_industry_classifications),
        joinedload(Company.domain_classifications),
        joinedload(Company.products),
        joinedload(Company.services),
        joinedload(Company.leadership),
        joinedload(Company.locations),
        joinedload(Company.news),
        joinedload(Company.documents),
        joinedload(Company.customer_list),
        joinedload(Company.partner_list),
        joinedload(Company.changes)
    ).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Count metrics
    products_count = len(company.products)
    services_count = len(company.services)
    customers_count = len(company.customer_list)
    partners_count = len(company.partner_list)
    locations_count = len(company.locations)
    news_count = len(company.news)
    documents_count = len(company.documents)
    changes_count = len(company.changes)
    
    # AI Insights (simplified - would normally call AI service)
    ai_insights = {
        "summary": company.business_summary or company.short_description or "No summary available",
        "key_strengths": company.core_competencies[:5] if company.core_competencies else [],
        "industries": [i.name for i in company.industry_classifications],
        "technologies": [t.name for t in company.technology_areas_list] if hasattr(company, 'technology_areas_list') else [],
        "risk_factors": ["Limited information available"] if not company.business_summary else [],
        "opportunities": ["Expansion potential"] if company.is_monitored else []
    }
    
    # Change timeline
    change_timeline = sorted(
        company.changes,
        key=lambda x: x.detected_at if x.detected_at else datetime.min,
        reverse=True
    )[:20]
    
    return CompanyDashboard(
        company=CompanyResponse.model_validate(company),
        products_count=products_count,
        services_count=services_count,
        customers_count=customers_count,
        partners_count=partners_count,
        locations_count=locations_count,
        news_count=news_count,
        documents_count=documents_count,
        changes_count=changes_count,
        ai_insights=ai_insights,
        change_timeline=[ChangeResponse.model_validate(c) for c in change_timeline]
    )