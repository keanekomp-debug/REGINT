"""Ingestion endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from uuid import UUID
from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.jobs import Job
from app.schemas.ingestion import IngestionRequest, JobResponse

router = APIRouter()

@router.post("/start", response_model=JobResponse)
async def start_ingestion(
    request: IngestionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Start manual ingestion job"""
    # Create job record
    job = Job(
        job_type="ingestion",
        country_code="BR",
        date_from=request.date_from,
        date_to=request.date_to,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # TODO: Trigger actual ingestion pipeline
    # For now, just return the job ID
    
    return {
        "job_id": str(job.id),
        "status": job.status,
        "date_from": job.date_from,
        "date_to": job.date_to
    }

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get job status"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": str(job.id),
        "status": job.status,
        "total_items": job.total_items,
        "processed_items": job.processed_items,
        "failed_items": job.failed_items,
        "date_from": job.date_from.isoformat() if job.date_from else None,
        "date_to": job.date_to.isoformat() if job.date_to else None
    }
