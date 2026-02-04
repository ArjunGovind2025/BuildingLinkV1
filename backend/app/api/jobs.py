"""Jobs API: POST /api/jobs, GET /api/jobs/:id."""
import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job
from app.schemas import JobResponse, JobStatus
from app.config import settings
from app.workers.process_job import run_pipeline_background

router = APIRouter()
log = logging.getLogger("app.api.jobs")

# Cloud Run max request body is 32MB; reject larger early
CLOUD_RUN_MAX_BYTES = 32 * 1024 * 1024
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
    request: Request,
    video: UploadFile = File(..., alias="video"),
    db: Session = Depends(get_db),
):
    content_length = request.headers.get("content-length")
    filename = video.filename or "(no filename)"
    log.info("create_job start filename=%s content_type=%s content_length=%s", filename, video.content_type, content_length)

    # Reject over Cloud Run limit before reading body (avoids silent failure)
    if content_length:
        try:
            cl = int(content_length)
            if cl > CLOUD_RUN_MAX_BYTES:
                log.warning("create_job rejected content_length %s > 32MB", cl)
                raise HTTPException(
                    413,
                    f"File too large. Maximum size is 32MB (Cloud Run limit). Got {cl / 1024 / 1024:.1f}MB.",
                )
        except ValueError:
            pass  # ignore bad content-length

    # Allow by content-type or by file extension when type is missing (e.g. some browsers/curl)
    ext = (Path(video.filename or "video").suffix or ".mp4").lower()
    if video.content_type not in ALLOWED_TYPES:
        if ext not in (".mp4", ".webm"):
            log.warning("create_job invalid content_type=%s filename=%s", video.content_type, filename)
            raise HTTPException(400, f"Invalid type. Allowed: {ALLOWED_TYPES}")
        log.info("create_job accepting by extension ext=%s (content_type=%s)", ext, video.content_type)

    try:
        content = await video.read()
    except Exception as e:
        log.exception("create_job failed reading body: %s", e)
        raise HTTPException(500, f"Failed to read upload: {e!s}")

    log.info("create_job body read size=%s bytes", len(content))

    if len(content) > MAX_SIZE:
        raise HTTPException(413, f"File too large. Maximum is {settings.max_upload_mb}MB.")

    job_id = str(uuid.uuid4())
    job_dir = settings.storage_root / "jobs" / job_id
    job_dir.mkdir(parents=True)
    video_path = job_dir / f"video{ext}"
    video_path.write_bytes(content)
    log.info("create_job wrote file path=%s", video_path)

    job = Job(
        id=job_id,
        status="pending",
        video_path=str(video_path),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    run_pipeline_background(job_id)
    log.info("create_job success job_id=%s", job_id)
    return job_to_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job_to_response(job)
