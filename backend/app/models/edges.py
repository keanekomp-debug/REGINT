"""Edge model (relationships)"""
from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Edge(Base):
    __tablename__ = "edges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    source_node_type = Column(String, nullable=False)
    source_node_id = Column(UUID(as_uuid=True), nullable=False)
    
    edge_type = Column(String, nullable=False)
    
    target_node_type = Column(String, nullable=False)
    target_node_id = Column(UUID(as_uuid=True), nullable=False)
    
    source_publication_id = Column(UUID(as_uuid=True), ForeignKey("publications.id"), nullable=False)
    text_span = Column(Text)
    text_span_offset = Column(Integer)
    extraction_method = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    ai_extraction_id = Column(UUID(as_uuid=True), ForeignKey("ai_extractions.id"))
    
    asserted_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    deactivated_at = Column(DateTime(timezone=True))
    
    properties = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
