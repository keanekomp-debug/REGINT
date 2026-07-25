"""Publication endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from uuid import UUID
from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.publications import Publication

router = APIRouter()

@router.get("/")
async def list_publications(
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List publications"""
    query = db.query(Publication)
    
    if date_from:
        query = query.filter(Publication.publication_date >= date_from)
    if date_to:
        query = query.filter(Publication.publication_date <= date_to)
    if status:
        query = query.filter(Publication.status == status)
    
    publications = query.order_by(Publication.publication_date.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "publication_date": p.publication_date.isoformat(),
            "status": p.status,
            "url": p.url
        }
        for p in publications
    ]

@router.get("/{publication_id}")
async def get_publication(
    publication_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get publication details"""
    publication = db.query(Publication).filter(Publication.id == publication_id).first()
    
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    return {
        "id": str(publication.id),
        "title": publication.title,
        "publication_date": publication.publication_date.isoformat(),
        "status": publication.status,
        "url": publication.url,
        "section": publication.section,
        "page": publication.page
    }
