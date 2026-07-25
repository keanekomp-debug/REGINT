"""Dashboard endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.publications import Publication
from app.models.companies import Company
from app.models.edges import Edge

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get dashboard statistics"""
    today = date.today()
    last_7_days = today - timedelta(days=7)
    
    # Publications today
    publications_today = db.query(func.count(Publication.id)).filter(
        Publication.publication_date == today
    ).scalar()
    
    # Total publications
    total_publications = db.query(func.count(Publication.id)).scalar()
    
    # Total companies
    total_companies = db.query(func.count(Company.id)).filter(
        Company.is_active == True,
        Company.deleted_at == None
    ).scalar()
    
    # Total edges
    total_edges = db.query(func.count(Edge.id)).filter(
        Edge.is_active == True
    ).scalar()
    
    return {
        "publications_today": publications_today,
        "total_publications": total_publications,
        "total_companies": total_companies,
        "total_edges": total_edges
    }

@router.get("/recent-publications")
async def get_recent_publications(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get recent publications"""
    publications = db.query(Publication).order_by(
        Publication.publication_date.desc()
    ).limit(limit).all()
    
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
