"""Search endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.companies import Company
from app.models.manufacturers import Manufacturer
from app.models.products import Product
from app.models.publications import Publication

router = APIRouter()

@router.get("/")
async def global_search(
    q: str = Query(..., min_length=2),
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Global search across all entities"""
    search_term = f"%{q}%"
    
    # Search companies
    companies = db.query(Company).filter(
        Company.is_active == True,
        Company.deleted_at == None,
        Company.name_normalized.ilike(search_term)
    ).limit(limit // 4).all()
    
    # Search manufacturers
    manufacturers = db.query(Manufacturer).filter(
        Manufacturer.is_active == True,
        Manufacturer.deleted_at == None,
        Manufacturer.name_normalized.ilike(search_term)
    ).limit(limit // 4).all()
    
    # Search products
    products = db.query(Product).filter(
        Product.is_active == True,
        Product.deleted_at == None,
        Product.name_normalized.ilike(search_term)
    ).limit(limit // 4).all()
    
    # Search publications
    publications = db.query(Publication).filter(
        or_(
            Publication.title.ilike(search_term),
            Publication.plain_text.ilike(search_term)
        )
    ).limit(limit // 4).all()
    
    results = []
    
    for c in companies:
        results.append({
            "type": "company",
            "id": str(c.id),
            "name": c.name,
            "metadata": {"tax_id": c.tax_id}
        })
    
    for m in manufacturers:
        results.append({
            "type": "manufacturer",
            "id": str(m.id),
            "name": m.name,
            "metadata": {"tax_id": m.tax_id}
        })
    
    for p in products:
        results.append({
            "type": "product",
            "id": str(p.id),
            "name": p.brand_name,
            "metadata": {}
        })
    
    for pub in publications:
        results.append({
            "type": "publication",
            "id": str(pub.id),
            "name": pub.title,
            "metadata": {"date": pub.publication_date.isoformat()}
        })
    
    return {"results": results, "total": len(results)}
