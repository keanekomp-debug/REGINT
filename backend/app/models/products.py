"""Product model"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_name = Column(String, nullable=False)
    name_normalized = Column(String, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    country_code = Column(String(2), ForeignKey("countries.code"))
    
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True))
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
