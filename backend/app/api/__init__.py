from fastapi import APIRouter
from app.api.companies import router as companies_router
from app.api.search import router as search_router
from app.api.intelligence import router as intelligence_router, chat_router
from app.api.monitoring import router as monitoring_router, dashboard_router

api_router = APIRouter()

api_router.include_router(companies_router)
api_router.include_router(search_router)
api_router.include_router(intelligence_router)
api_router.include_router(chat_router)
api_router.include_router(monitoring_router)
api_router.include_router(dashboard_router)