"""Job model for video processing pipeline."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, JSON
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    status = Column(String(32), nullable=False, default="pending")  # pending | processing | completed | failed
    video_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    spec = Column(JSON, nullable=True)
    acceptance_criteria = Column(JSON, nullable=True)
    evidence_map = Column(JSON, nullable=True)  # screenshot_id -> path/url
    transcript_segments = Column(Integer, nullable=True)
    screenshots_captured = Column(Integer, nullable=True)
    screenshots_analyzed = Column(Integer, nullable=True)
