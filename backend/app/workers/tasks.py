from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.models import (
    Company, Industry, SubIndustry, Domain, EngineeringDiscipline, Technology,
    Product, Service, Leadership, Location, Customer, Partner, News, Document,
    Snapshot, Change, Embedding
)
from app.scraper.scraper import CompanyScraper
from datetime import datetime, timedelta
from uuid import UUID
import json
import httpx
import numpy as np


@celery_app.task(bind=True, max_retries=3)
def scrape_company_task(self, url: str, company_id: str = None):
    """
    Scrape a company website and extract information.
    """
    db = SessionLocal()
    try:
        scraper = CompanyScraper()
        
        # Scrape the website
        scraped_data = scraper.scrape(url)
        
        if not scraped_data:
            raise Exception(f"Failed to scrape {url}")
        
        # Process and store the data
        if company_id:
            company = db.query(Company).filter(Company.id == UUID(company_id)).first()
            if company:
                # Update existing company
                update_company_from_scrape(db, company, scraped_data)
        else:
            # Create new company
            create_company_from_scrape(db, scraped_data)
        
        db.commit()
        
        return {
            "status": "success",
            "url": url,
            "company_id": company_id
        }
        
    except Exception as e:
        self.retry(exc=e, countdown=60)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def check_for_changes_task(self, company_id: str):
    """
    Check a company for changes since last snapshot.
    """
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == UUID(company_id)).first()
        
        if not company:
            raise Exception(f"Company {company_id} not found")
        
        # Get the latest snapshot
        latest_snapshot = db.query(Snapshot).filter(
            Snapshot.company_id == company.id
        ).order_by(Snapshot.created_at.desc()).first()
        
        # Create a new snapshot of current state
        current_data = get_company_snapshot_data(company)
        
        if latest_snapshot:
            # Compare with previous snapshot
            changes = compare_snapshots(db, company, latest_snapshot.snapshot_data, current_data)
            
            for change in changes:
                db_change = Change(
                    company_id=company.id,
                    change_type=change["type"],
                    description=change["description"],
                    previous_value=change.get("previous"),
                    new_value=change.get("new"),
                    severity=change.get("severity", "low")
                )
                db.add(db_change)
        else:
            # First snapshot - no changes to detect
            pass
        
        # Create new snapshot
        snapshot = Snapshot(
            company_id=company.id,
            snapshot_data=current_data,
            products_snapshot=[{"name": p.name, "description": p.description} for p in company.products],
            services_snapshot=[{"name": s.name, "description": s.description} for s in company.services],
            leadership_snapshot=[{"name": l.name, "position": l.position} for l in company.leadership],
            locations_snapshot=[{"name": loc.name, "city": loc.city, "country": loc.country} for loc in company.locations]
        )
        db.add(snapshot)
        
        # Update last scraped time
        company.last_scraped_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "success",
            "company_id": company_id,
            "changes_detected": len(changes) if 'changes' in dir() else 0
        }
        
    except Exception as e:
        self.retry(exc=e, countdown=60)
    finally:
        db.close()


@celery_app.task
def check_all_monitored_companies():
    """
    Periodic task to check all monitored companies for changes.
    """
    db = SessionLocal()
    try:
        monitored_companies = db.query(Company).filter(
            Company.is_monitored == True
        ).all()
        
        for company in monitored_companies:
            # Queue a check for each monitored company
            check_for_changes_task.delay(str(company.id))
        
        return {
            "status": "success",
            "companies_queued": len(monitored_companies)
        }
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_snapshots():
    """
    Periodic task to clean up old snapshots beyond retention period.
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=settings.SNAPSHOT_RETENTION_DAYS)
        
        old_snapshots = db.query(Snapshot).filter(
            Snapshot.created_at < cutoff_date
        ).all()
        
        count = len(old_snapshots)
        
        for snapshot in old_snapshots:
            db.delete(snapshot)
        
        db.commit()
        
        return {
            "status": "success",
            "snapshots_deleted": count
        }
        
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def generate_embeddings_task(self, entity_type: str, entity_id: str):
    """
    Generate embeddings for a company, product, service, etc.
    """
    db = SessionLocal()
    try:
        # Get the content to embed
        content = ""
        entity_uuid = UUID(entity_id)
        
        if entity_type == "company":
            entity = db.query(Company).filter(Company.id == entity_uuid).first()
            if entity:
                content = f"{entity.name}. {entity.description or ''} {entity.business_summary or ''}"
                content += " " + " ".join(entity.capabilities or [])
                content += " " + " ".join(entity.expertise_areas or [])
        elif entity_type == "product":
            entity = db.query(Product).filter(Product.id == entity_uuid).first()
            if entity:
                content = f"{entity.name}. {entity.description or ''}"
                content += " " + " ".join(entity.features or [])
                content += " " + " ".join(entity.use_cases or [])
        elif entity_type == "service":
            entity = db.query(Service).filter(Service.id == entity_uuid).first()
            if entity:
                content = f"{entity.name}. {entity.description or ''}"
        
        if not content:
            raise Exception(f"No content to embed for {entity_type} {entity_id}")
        
        # Generate embedding using Ollama
        async def generate():
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                    json={
                        "model": settings.OLLAMA_EMBED_MODEL,
                        "prompt": content
                    }
                )
                return response.json()
        
        # Run the async function
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(generate())
        finally:
            loop.close()
        
        embedding = result.get("embedding", [])
        
        if embedding:
            # Store or update the embedding
            existing = db.query(Embedding).filter(
                Embedding.entity_type == entity_type,
                Embedding.entity_id == entity_uuid
            ).first()
            
            if existing:
                existing.embedding = embedding
                existing.content = content
                existing.updated_at = datetime.utcnow()
            else:
                db_embedding = Embedding(
                    entity_type=entity_type,
                    entity_id=entity_uuid,
                    content=content,
                    embedding=embedding
                )
                db.add(db_embedding)
            
            db.commit()
        
        return {
            "status": "success",
            "entity_type": entity_type,
            "entity_id": entity_id
        }
        
    except Exception as e:
        self.retry(exc=e, countdown=60)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def extract_intelligence_task(self, content: str, content_type: str, company_id: str = None):
    """
    Extract structured intelligence from content using AI.
    """
    db = SessionLocal()
    try:
        async def extract():
            async with httpx.AsyncClient(timeout=120.0) as client:
                prompt = f"""Analyze the following {content_type} content and extract structured information.

Content:
{content[:10000]}  # Limit content size

Return a JSON object with:
{{
    "company_data": {{...}},
    "products": [...],
    "services": [...],
    "technologies": [...],
    "industries": [...],
    "domains": [...]
}}
"""
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                return response.json()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(extract())
        finally:
            loop.close()
        
        extracted_text = result.get("response", "")
        
        # Parse JSON from response
        try:
            json_start = extracted_text.find('{')
            json_end = extracted_text.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                intelligence = json.loads(extracted_text[json_start:json_end])
            else:
                intelligence = {}
        except json.JSONDecodeError:
            intelligence = {}
        
        # Store the extracted intelligence
        if company_id:
            company = db.query(Company).filter(Company.id == UUID(company_id)).first()
            if company and "company_data" in intelligence:
                update_company_intelligence(db, company, intelligence)
                db.commit()
        
        return {
            "status": "success",
            "intelligence": intelligence
        }
        
    except Exception as e:
        self.retry(exc=e, countdown=60)
    finally:
        db.close()


# Helper functions
def get_company_snapshot_data(company):
    """Get a snapshot of company data."""
    return {
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


def compare_snapshots(db, company, old_data, new_data):
    """Compare two snapshots and detect changes."""
    changes = []
    
    # Compare basic fields
    for key in ["name", "description", "headquarters", "city", "country"]:
        old_val = old_data.get(key)
        new_val = new_data.get(key)
        if old_val != new_val:
            changes.append({
                "type": f"field_change_{key}",
                "description": f"{key.title()} changed from '{old_val}' to '{new_val}'",
                "previous": old_val,
                "new": new_val,
                "severity": "medium"
            })
    
    # Compare competencies
    old_competencies = set(old_data.get("core_competencies", []) or [])
    new_competencies = set(new_data.get("core_competencies", []) or [])
    
    added_competencies = new_competencies - old_competencies
    removed_competencies = old_competencies - new_competencies
    
    if added_competencies:
        changes.append({
            "type": "new_competencies",
            "description": f"Added competencies: {', '.join(added_competencies)}",
            "new": list(added_competencies),
            "severity": "low"
        })
    
    if removed_competencies:
        changes.append({
            "type": "removed_competencies",
            "description": f"Removed competencies: {', '.join(removed_competencies)}",
            "previous": list(removed_competencies),
            "severity": "low"
        })
    
    # Compare products
    old_products = {p["name"] for p in company.products}
    new_products = {p["name"] for p in db.query(Product).filter(Product.company_id == company.id).all()}
    
    added_products = new_products - old_products
    removed_products = old_products - new_products
    
    if added_products:
        changes.append({
            "type": "new_products",
            "description": f"New products: {', '.join(added_products)}",
            "new": list(added_products),
            "severity": "medium"
        })
    
    if removed_products:
        changes.append({
            "type": "removed_products",
            "description": f"Removed products: {', '.join(removed_products)}",
            "previous": list(removed_products),
            "severity": "medium"
        })
    
    # Compare services
    old_services = {s["name"] for s in company.services}
    new_services = {s["name"] for s in db.query(Service).filter(Service.company_id == company.id).all()}
    
    added_services = new_services - old_services
    removed_services = old_services - new_services
    
    if added_services:
        changes.append({
            "type": "new_services",
            "description": f"New services: {', '.join(added_services)}",
            "new": list(added_services),
            "severity": "medium"
        })
    
    if removed_services:
        changes.append({
            "type": "removed_services",
            "description": f"Removed services: {', '.join(removed_services)}",
            "previous": list(removed_services),
            "severity": "medium"
        })
    
    return changes


def update_company_from_scrape(db, company, scraped_data):
    """Update company with scraped data."""
    if "title" in scraped_data:
        company.name = scraped_data["title"]
    
    if "description" in scraped_data:
        company.description = scraped_data["description"]
    
    if "text_content" in scraped_data:
        # Store additional content in metadata
        metadata = company.metadata_json or {}
        metadata["scraped_content"] = scraped_data["text_content"][:50000]  # Limit size
        company.metadata_json = metadata


def create_company_from_scrape(db, scraped_data):
    """Create a new company from scraped data."""
    company = Company(
        name=scraped_data.get("title", "Unknown Company"),
        description=scraped_data.get("description"),
        website=scraped_data.get("url"),
    )
    db.add(company)
    
    if "text_content" in scraped_data:
        metadata = company.metadata_json or {}
        metadata["scraped_content"] = scraped_data["text_content"][:50000]
        company.metadata_json = metadata
    
    return company


def update_company_intelligence(db, company, intelligence):
    """Update company with extracted intelligence."""
    company_data = intelligence.get("company_data", {})
    
    if "business_summary" in company_data:
        company.business_summary = company_data["business_summary"]
    
    if "business_model" in company_data:
        company.business_model = company_data["business_model"]
    
    if "core_competencies" in company_data:
        company.core_competencies = company_data["core_competencies"]
    
    if "capabilities" in company_data:
        company.capabilities = company_data["capabilities"]
    
    if "target_customers" in company_data:
        company.target_customers = company_data["target_customers"]
    
    if "industries_served" in company_data:
        company.industries_served = company_data["industries_served"]
    
    # Create products
    for product_data in intelligence.get("products", []):
        product = Product(
            company_id=company.id,
            name=product_data.get("name", "Unknown Product"),
            description=product_data.get("description"),
            category=product_data.get("category"),
            features=product_data.get("features", []),
            use_cases=product_data.get("use_cases", [])
        )
        db.add(product)
    
    # Create services
    for service_data in intelligence.get("services", []):
        service = Service(
            company_id=company.id,
            name=service_data.get("name", "Unknown Service"),
            description=service_data.get("description"),
            category=service_data.get("category")
        )
        db.add(service)
    
    # Handle industries
    for industry_name in intelligence.get("industries", []):
        industry = db.query(Industry).filter(Industry.name == industry_name).first()
        if not industry:
            industry = Industry(name=industry_name)
            db.add(industry)
            db.flush()
        if industry not in company.industry_classifications:
            company.industry_classifications.append(industry)
    
    # Handle technologies
    for tech_name in intelligence.get("technologies", []):
        tech = db.query(Technology).filter(Technology.name == tech_name).first()
        if not tech:
            tech = Technology(name=tech_name)
            db.add(tech)
            db.flush()
        if tech not in company.technology_areas_list:
            company.technology_areas_list.append(tech)