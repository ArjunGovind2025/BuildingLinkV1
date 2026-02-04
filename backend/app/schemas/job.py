"""Pydantic schemas for Job API."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class JobCreate(BaseModel):
    pass  # video comes as multipart


class JobStatus(BaseModel):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class JobResponse(JobStatus):
    video_path: str | None = None
    spec: dict[str, Any] | None = None
    acceptance_criteria: dict[str, Any] | None = None
    evidence_map: dict[str, str] | None = None
    transcript_segments: int | None = None
    screenshots_captured: int | None = None
    screenshots_analyzed: int | None = None
