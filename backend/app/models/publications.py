"""Publication model"""
from sqlalchemy import Column, String, Date, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Publication(Base):
    __tablename__ = "publications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    country_code = Column(String(2), ForeignKey("countries.code"), nullable=False)
    
    publication_date = Column(Date, nullable=False)
    title = Column(Text, nullable=False)
    section = Column(Text)
    page = Column(Text)
    url = Column(Text, nullable=False)
    external_id = Column(Text)
    
    html_content = Column(Text)
    plain_text = Column(Text)
    checksum_sha256 = Column(Text)
    
    status = Column(String(20), nullable=False, default="pending_search")
    
    download_attempts = Column(Integer, default=0)
    parse_attempts = Column(Integer, default=0)
    metadata_ = Column("metadata", JSONB, default={})
    
    found_at = Column(DateTime(timezone=True))
    downloaded_at = Column(DateTime(timezone=True))
    parsed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
