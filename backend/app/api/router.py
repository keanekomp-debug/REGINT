"""Main API router"""
from fastapi import APIRouter
from app.api.endpoints import auth, dashboard, ingestion, entities, publications, search

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(entities.router, prefix="/entities", tags=["entities"])
api_router.include_router(publications.router, prefix="/publications", tags=["publications"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
