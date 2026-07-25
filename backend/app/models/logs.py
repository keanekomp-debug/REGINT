"""Log model"""
from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    level = Column(String, nullable=False)
    category = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSONB, default={})
    
    url = Column(Text)
    publication_id = Column(UUID(as_uuid=True), ForeignKey("publications.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
