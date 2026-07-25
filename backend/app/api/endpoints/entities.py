"""Entity endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.companies import Company
from app.models.manufacturers import Manufacturer
from app.models.products import Product

router = APIRouter()

@router.get("/companies")
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List companies"""
    query = db.query(Company).filter(
        Company.is_active == True,
        Company.deleted_at == None
    )
    
    if search:
        query = query.filter(Company.name_normalized.ilike(f"%{search}%"))
    
    companies = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "tax_id": c.tax_id,
            "country_code": c.country_code
        }
        for c in companies
    ]

@router.get("/companies/{company_id}")
async def get_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get company details"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True,
        Company.deleted_at == None
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "id": str(company.id),
        "name": company.name,
        "tax_id": company.tax_id,
        "country_code": company.country_code,
        "created_at": company.created_at.isoformat()
    }

@router.get("/manufacturers")
async def list_manufacturers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List manufacturers"""
    manufacturers = db.query(Manufacturer).filter(
        Manufacturer.is_active == True,
        Manufacturer.deleted_at == None
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "tax_id": m.tax_id,
            "country_code": m.country_code
        }
        for m in manufacturers
    ]

@router.get("/products")
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List products"""
    products = db.query(Product).filter(
        Product.is_active == True,
        Product.deleted_at == None
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(p.id),
            "brand_name": p.brand_name,
            "company_id": str(p.company_id) if p.company_id else None,
            "country_code": p.country_code
        }
        for p in products
    ]
