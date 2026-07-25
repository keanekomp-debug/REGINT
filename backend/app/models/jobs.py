"""Job model"""
from sqlalchemy import Column, String, Date, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String, nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"))
    country_code = Column(String(2), ForeignKey("countries.code"))
    
    date_from = Column(Date)
    date_to = Column(Date)
    config = Column(JSONB, default={})
    
    status = Column(String, nullable=False, default="pending")
    
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    skipped_items = Column(Integer, default=0)
    checkpoint = Column(JSONB)
    
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    result_summary = Column(JSONB, default={})
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
