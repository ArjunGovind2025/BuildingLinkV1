"""Jobs API: POST /api/jobs, GET /api/jobs/:id."""
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job
from app.schemas import JobResponse, JobStatus
from app.config import settings
from app.workers.process_job import run_pipeline_background

router = APIRouter()

MAX_SIZE = settings.max_upload_mb * 1024 * 1024
ALLOWED_TYPES = settings.allowed_video_types


def job_to_response(job: Job, base_url: str = "") -> JobResponse:
    return JobResponse(
        id=job.id,
        status=job.status,
        video_path=job.video_path,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message,
        spec=job.spec,
        acceptance_criteria=job.acceptance_criteria,
        evidence_map=job.evidence_map,
        transcript_segments=job.transcript_segments,
        screenshots_captured=job.screenshots_captured,
        screenshots_analyzed=job.screenshots_analyzed,
    )


@router.post("/jobs", response_model=JobResponse)
async def create_job(
    video: UploadFile = File(..., alias="video"),
    db: Session = Depends(get_db),
):
    if video.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Invalid type. Allowed: {ALLOWED_TYPES}")
    content = await video.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, f"File too large. Max {settings.max_upload_mb}MB")
    job_id = str(uuid.uuid4())
    job_dir = settings.storage_root / "jobs" / job_id
    job_dir.mkdir(parents=True)
    ext = Path(video.filename or "video").suffix or ".mp4"
    video_path = job_dir / f"video{ext}"
    video_path.write_bytes(content)
    job = Job(
        id=job_id,
        status="pending",
        video_path=str(video_path),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    run_pipeline_background(job_id)
    return job_to_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job_to_response(job)
