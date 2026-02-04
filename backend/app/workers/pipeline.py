"""Full pipeline: media -> transcription -> vision -> grounding -> spec -> AC."""
import json
from pathlib import Path
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Job
from app.config import settings
from app.services.media import extract_audio, capture_screenshots
from app.services.transcription import transcribe_audio
from app.services.vision import describe_screenshots
from app.services.grounding import build_grounded_chunks
from app.services.spec_extraction import extract_spec
from app.services.acceptance_criteria import generate_acceptance_criteria


def process_job(job_id: str) -> None:
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or job.status not in ("pending",):
            return
        job_dir = Path(settings.storage_root) / "jobs" / job_id
        if not job_dir.exists():
            _fail(db, job, "Job directory not found")
            return
        job.status = "processing"
        db.commit()

        # 1. Media
        video_path = job_dir / "video.mp4"
        for p in job_dir.glob("video.*"):
            video_path = p
            break
        audio_path = job_dir / "audio.wav"
        extract_audio(str(video_path), str(audio_path))
        screenshots_dir = job_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        capture_screenshots(str(video_path), str(screenshots_dir))
        manifest_path = screenshots_dir / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            job.screenshots_captured = len(manifest)
        db.commit()

        # 2. Transcription
        transcript_path = job_dir / "transcript.json"
        transcribe_audio(str(audio_path), str(transcript_path))
        if transcript_path.exists():
            transcript_data = json.loads(transcript_path.read_text())
            job.transcript_segments = len(transcript_data.get("segments", []))
        db.commit()

        # 3. Vision (per screenshot)
        describe_screenshots(job_dir)
        cache_vision = job_dir / "cache" / "vision"
        if cache_vision.exists():
            job.screenshots_analyzed = len(list(cache_vision.glob("*.json")))
        db.commit()

        # 4. Grounding
        grounded_path = job_dir / "grounded_chunks.json"
        build_grounded_chunks(job_dir, str(grounded_path))

        # 5. Spec extraction (pass full transcript so extraction is exhaustive)
        spec_path = job_dir / "spec.json"
        spec_data = extract_spec(str(grounded_path), str(spec_path), transcript_path=transcript_path)
        job.spec = spec_data
        db.commit()

        # 6. Acceptance criteria (generated nested under user stories)
        ac_path = job_dir / "acceptance_criteria.json"
        ac_data = generate_acceptance_criteria(str(spec_path), str(ac_path), job_dir)
        # Merge ACs into spec.user_stories (each story gets its acceptance_criteria)
        # Preserve spec fields (persona, story_text, tags) and only merge acceptance_criteria
        ac_stories = ac_data.get("user_stories", [])
        if ac_stories:
            spec_user_stories = spec_data.get("user_stories", [])
            # Match by id or index and merge acceptance_criteria only
            for i, spec_us in enumerate(spec_user_stories):
                spec_us_id = spec_us.get("id", f"us-{i+1}")
                # Find matching AC story
                matched = False
                for ac_us in ac_stories:
                    if ac_us.get("id") == spec_us_id or (i < len(ac_stories) and ac_stories[i].get("id") == ac_us.get("id")):
                        spec_us["acceptance_criteria"] = ac_us.get("acceptance_criteria", [])
                        matched = True
                        break
                if not matched:
                    # No match found, try by index
                    if i < len(ac_stories):
                        spec_us["acceptance_criteria"] = ac_stories[i].get("acceptance_criteria", [])
                    else:
                        spec_us["acceptance_criteria"] = []
            spec_data["user_stories"] = spec_user_stories
            # Update spec.json with merged data
            Path(spec_path).write_text(json.dumps(spec_data, indent=2))
            job.spec = spec_data
        job.acceptance_criteria = ac_data
        manifest_path = job_dir / "screenshots" / "manifest.json"
        evidence_map = {}
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            for entry in manifest:
                sid = str(entry.get("timestamp_ms", entry.get("path", "")))
                evidence_map[sid] = entry.get("path", f"{sid}.png")
        job.evidence_map = evidence_map
        job.status = "completed"
        if job.screenshots_captured is None and manifest_path.exists():
            job.screenshots_captured = len(json.loads(manifest_path.read_text()))
        db.commit()
    except Exception as e:
        _fail(db, job, str(e))
    finally:
        db.close()


def _fail(db: Session, job: Job | None, message: str) -> None:
    if job:
        job.status = "failed"
        job.error_message = message
        db.commit()
