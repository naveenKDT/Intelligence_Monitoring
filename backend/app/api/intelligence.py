from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
import httpx
import json

from app.core.database import get_db
from app.core.config import settings
from app.models.models import (
    Company, Industry, SubIndustry, Domain, EngineeringDiscipline, Technology,
    Product, Service, Customer, Partner, Leadership, Location,
    News, Document, Snapshot, Change, ChatMessage
)
from app.schemas.schemas import (
    IntelligenceExtractRequest, IntelligenceExtractResponse,
    ClassificationRequest, ClassificationResponse,
    CompanyResponse, ChatRequest, ChatResponse, ChatMessageCreate, ChatMessageResponse,
    ChangeCreate, ChangeResponse
)
from app.workers.tasks import extract_intelligence_task, classify_company_task

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.post("/extract", response_model=IntelligenceExtractResponse)
async def extract_intelligence(
    request: IntelligenceExtractRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Extract structured intelligence from raw content using AI.
    This endpoint processes content and returns structured data about companies, products, etc.
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Call Ollama for intelligence extraction
            prompt = f"""Analyze the following content and extract structured information about companies, products, services, technologies, and industries.

Content to analyze:
{request.content}

Return a JSON object with the following structure:
{{
    "company_data": {{
        "name": "Company name if found",
        "description": "Company description",
        "short_description": "A brief 2-3 sentence description",
        "business_summary": "Summary of what the company does",
        "business_model": "How the company makes money",
        "core_competencies": ["list of core competencies"],
        "capabilities": ["list of capabilities"],
        "target_customers": ["list of target customer types"],
        "industries_served": ["list of industries served"]
    }},
    "products": [
        {{
            "name": "Product name",
            "description": "Product description",
            "category": "Product category",
            "features": ["list of features"],
            "use_cases": ["list of use cases"]
        }}
    ],
    "services": [
        {{
            "name": "Service name",
            "description": "Service description",
            "category": "Service category"
        }}
    ],
    "technologies": ["list of technologies mentioned"],
    "industries": ["list of industries"],
    "domains": ["list of domains"]
}}

Only include fields that have meaningful data. Return valid JSON only."""
            
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2048
                    }
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI service unavailable")
            
            result = response.json()
            extracted_text = result.get("response", "")
            
            # Parse the JSON from the response
            try:
                # Try to extract JSON from the response
                json_start = extracted_text.find('{')
                json_end = extracted_text.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = extracted_text[json_start:json_end]
                    intelligence = json.loads(json_str)
                else:
                    intelligence = {
                        "company_data": {},
                        "products": [],
                        "services": [],
                        "technologies": [],
                        "industries": [],
                        "domains": []
                    }
            except json.JSONDecodeError:
                intelligence = {
                    "company_data": {},
                    "products": [],
                    "services": [],
                    "technologies": [],
                    "industries": [],
                    "domains": []
                }
            
            return IntelligenceExtractResponse(**intelligence)
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence extraction failed: {str(e)}")


@router.post("/classify")
async def classify_company(
    request: ClassificationRequest,
    db: Session = Depends(get_db)
):
    """
    Classify a company into industries, domains, or technologies.
    """
    company = db.query(Company).filter(Company.id == request.company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            prompt = f"""Based on the following company information, classify it into relevant categories.

Company Name: {company.name}
Description: {company.description or company.short_description or "N/A"}
Business Summary: {company.business_summary or "N/A"}
Capabilities: {', '.join(company.capabilities) if company.capabilities else "N/A"}
Expertise Areas: {', '.join(company.expertise_areas) if company.expertise_areas else "N/A"}

Classification Type: {request.classification_type}

"""
            
            if request.classification_type == "industry":
                prompt += """Return a JSON array of industry classifications:
["Industry1", "Industry2", ...]"""
            elif request.classification_type == "domain":
                prompt += """Return a JSON array of domain classifications:
["Domain1", "Domain2", ...]"""
            elif request.classification_type == "technology":
                prompt += """Return a JSON array of technology areas:
["Technology1", "Technology2", ...]"""
            else:
                prompt += """Return a JSON object with classifications:
{{"industries": [], "domains": [], "technologies": []}}"""
            
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1024
                    }
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI service unavailable")
            
            result = response.json()
            classifications_text = result.get("response", "")
            
            # Parse classifications
            try:
                json_start = classifications_text.find('[')
                json_end = classifications_text.rfind(']') + 1
                if json_start == -1:
                    json_start = classifications_text.find('{')
                    json_end = classifications_text.rfind('}') + 1
                
                if json_start != -1 and json_end != 0:
                    json_str = classifications_text[json_start:json_end]
                    classifications = json.loads(json_str)
                else:
                    classifications = []
            except json.JSONDecodeError:
                classifications = []
            
            return ClassificationResponse(
                classifications=[{"name": c, "confidence": 0.8} for c in (classifications if isinstance(classifications, list) else [])],
                confidence=0.8
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.get("/summary/{company_id}")
async def get_company_summary(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Generate an AI summary of a company.
    """
    company = db.query(Company).options(
        joinedload(Company.industry_classifications),
        joinedload(Company.products),
        joinedload(Company.services),
        joinedload(Company.technology_areas_list)
    ).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            industries = [i.name for i in company.industry_classifications]
            products = [p.name for p in company.products]
            services = [s.name for s in company.services]
            technologies = [t.name for t in company.technology_areas_list]
            
            prompt = f"""Generate a comprehensive summary of the following company.

Company: {company.name}
Description: {company.description or "N/A"}
Business Summary: {company.business_summary or "N/A"}
Headquarters: {company.headquarters or "N/A"}
Founded: {company.founded_year or "N/A"}
Employee Range: {company.employee_range or "N/A"}
Industries: {', '.join(industries) if industries else "N/A"}
Products: {', '.join(products) if products else "N/A"}
Services: {', '.join(services) if services else "N/A"}
Technologies: {', '.join(technologies) if technologies else "N/A"}
Capabilities: {', '.join(company.capabilities) if company.capabilities else "N/A"}

Provide a well-structured summary covering:
1. What the company does
2. Key products and services
3. Industries served
4. Technology expertise
5. Market presence
"""
            
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 1024
                    }
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI service unavailable")
            
            result = response.json()
            summary = result.get("response", "")
            
            return {"summary": summary, "company_id": str(company_id)}
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


# Chat API
chat_router = APIRouter(prefix="/chat", tags=["Chat"])


@chat_router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with AI about companies and industry intelligence.
    """
    # Get company context if specified
    company_context = {}
    if request.company_id:
        company = db.query(Company).options(
            joinedload(Company.industry_classifications),
            joinedload(Company.products),
            joinedload(Company.services),
            joinedload(Company.technology_areas_list),
            joinedload(Company.customers),
            joinedload(Company.partners)
        ).filter(Company.id == request.company_id).first()
        
        if company:
            company_context = {
                "name": company.name,
                "description": company.description,
                "business_summary": company.business_summary,
                "industries": [i.name for i in company.industry_classifications],
                "products": [p.name for p in company.products],
                "services": [s.name for s in company.services],
                "technologies": [t.name for t in company.technology_areas_list],
                "capabilities": company.capabilities or [],
                "target_customers": company.target_customers or [],
                "headquarters": company.headquarters,
                "country": company.country
            }
    
    # Save user message
    user_message = ChatMessage(
        company_id=request.company_id,
        role="user",
        content=request.message,
        context=company_context if company_context else None
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Build context for the chat
            context_text = ""
            if company_context:
                context_text = f"""
The user is asking about the company: {company_context['name']}

Company Information:
- Description: {company_context.get('description', 'N/A')}
- Business Summary: {company_context.get('business_summary', 'N/A')}
- Industries: {', '.join(company_context.get('industries', [])) or 'N/A'}
- Products: {', '.join(company_context.get('products', [])) or 'N/A'}
- Services: {', '.join(company_context.get('services', [])) or 'N/A'}
- Technologies: {', '.join(company_context.get('technologies', [])) or 'N/A'}
- Capabilities: {', '.join(company_context.get('capabilities', [])) or 'N/A'}
- Target Customers: {', '.join(company_context.get('target_customers', [])) or 'N/A'}
- Headquarters: {company_context.get('headquarters', 'N/A')}, {company_context.get('country', 'N/A')}
"""
            
            prompt = f"""{context_text}

User Question: {request.message}

Please provide a helpful, accurate response based on the company information provided above. If the information is not available, say so. Keep your response concise and informative.
"""
            
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1024
                    }
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI service unavailable")
            
            result = response.json()
            ai_response = result.get("response", "")
            
            # Save AI response
            assistant_message = ChatMessage(
                company_id=request.company_id,
                role="assistant",
                content=ai_response,
                context=company_context if company_context else None
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            
            return ChatResponse(
                message=ai_response,
                conversation_id=request.company_id or user_message.id
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@chat_router.get("/history/{company_id}", response_model=List[ChatMessageResponse])
def get_chat_history(
    company_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a company.
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.company_id == company_id
    ).order_by(ChatMessage.created_at).limit(limit).all()
    
    return messages