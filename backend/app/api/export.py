"""Export API: GET /api/jobs/:id/export?format=md|json, PATCH /api/jobs/:id/spec (edit), POST regenerate AC."""
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job
from app.config import settings
from app.services.acceptance_criteria import generate_acceptance_criteria

router = APIRouter()


def _get_job_and_dir(job_id: str, db: Session):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    job_dir = Path(settings.storage_root) / "jobs" / job_id
    if not job_dir.exists():
        raise HTTPException(404, "Job artifacts not found")
    return job, job_dir


@router.get("/jobs/{job_id}/export")
def export_job(
    job_id: str,
    format: str = Query("md", alias="format"),
    db: Session = Depends(get_db),
):
    """Export as markdown or JSON (Jira/Linear friendly)."""
    job, job_dir = _get_job_and_dir(job_id, db)
    if job.status != "completed":
        raise HTTPException(400, "Job not completed")
    spec = job.spec or {}
    evidence_map = job.evidence_map or {}
    # User stories now have nested acceptance_criteria
    user_stories = spec.get("user_stories", []) or []

    if format == "md":
        lines = [
            "# Feature summary",
            "",
            spec.get("feature_summary", ""),
            "",
            "## User stories",
            "",
        ]
        for us in user_stories:
            title = us.get("title", "")
            persona = us.get("persona", "")
            story_text = us.get("story_text", "")
            tags = us.get("tags", [])
            desc = us.get("description", "")
            refs = us.get("evidence_refs", [])
            acs = us.get("acceptance_criteria", [])
            lines.append(f"### {title}")
            lines.append("")
            if persona:
                persona_str = ", ".join(persona) if isinstance(persona, list) else persona
                lines.append(f"**Persona:** {persona_str}")
                lines.append("")
            if story_text:
                lines.append(f"*{story_text}*")
                lines.append("")
            elif desc:
                lines.append(desc)
                lines.append("")
            if tags:
                lines.append(f"**Tags:** {', '.join(tags)}")
                lines.append("")
            if refs:
                lines.append("**Evidence:**")
                for r in refs:
                    ts = r.get("timestamp", 0)
                    excerpt = r.get("transcript_excerpt", "")[:200]
                    sid = r.get("screenshot_id", "")
                    lines.append(f"- {ts}ms | {sid} | {excerpt}...")
                lines.append("")
            if acs:
                lines.append("#### Acceptance criteria")
                lines.append("")
                for ac in acs:
                    ac_id = ac.get('id', '')
                    lines.append(f"**{ac_id}**")
                    lines.append("")
                    lines.append(f"**GIVEN** {ac.get('given', '')}")
                    lines.append("")
                    lines.append(f"**WHEN** {ac.get('when', '')}")
                    lines.append("")
                    lines.append(f"**THEN** {ac.get('then', '')}")
                    and_list = ac.get("and", [])
                    if and_list:
                        for and_item in and_list:
                            lines.append("")
                            lines.append(f"**AND** {and_item}")
                    lines.append("")
                    ac_refs = ac.get("evidence_refs", [])
                    if ac_refs:
                        lines.append("Evidence:")
                        for r in ac_refs:
                            ts = r.get("timestamp", 0)
                            excerpt = (r.get("transcript_excerpt", "") or "")[:200]
                            sid = r.get("screenshot_id", "")
                            lines.append(f"- {ts}ms | {sid} | {excerpt}...")
                        lines.append("")
            lines.append("")
        lines.append("## Open questions")
        lines.append("")
        for q in spec.get("open_questions", []) or []:
            lines.append(f"- {q}")
        return PlainTextResponse("\n".join(lines), media_type="text/markdown")
    elif format == "json":
        payload = {
            "feature_summary": spec.get("feature_summary", ""),
            "user_stories": user_stories,
            "open_questions": spec.get("open_questions", []),
            "evidence_map": evidence_map,
        }
        return JSONResponse(payload)
    raise HTTPException(400, "format must be md or json")


@router.get("/jobs/{job_id}/transcript")
def get_transcript(
    job_id: str,
    format: str = Query("txt", alias="format"),
    db: Session = Depends(get_db),
):
    """Download full transcript as JSON or plain text (one line per segment with timestamp)."""
    job, job_dir = _get_job_and_dir(job_id, db)
    transcript_path = job_dir / "transcript.json"
    if not transcript_path.exists():
        raise HTTPException(404, "Transcript not found")
    data = json.loads(transcript_path.read_text())
    segments = data.get("segments", [])

    if format == "json":
        return JSONResponse(data)
    if format == "txt":
        lines = []
        for s in segments:
            start = s.get("start", 0)
            end = s.get("end", 0)
            text = (s.get("text", "") or "").strip()
            # [MM:SS.mmm] text or [MM:SS.mmm - MM:SS.mmm] text
            start_m = int(start // 60)
            start_s = start % 60
            end_m = int(end // 60)
            end_s = end % 60
            ts = f"[{start_m:02d}:{start_s:06.3f} - {end_m:02d}:{end_s:06.3f}]"
            lines.append(f"{ts} {text}")
        body = "\n".join(lines)
        return PlainTextResponse(body, media_type="text/plain")
    raise HTTPException(400, "format must be json or txt")


@router.patch("/jobs/{job_id}/spec")
def update_spec(job_id: str, body: dict = Body(...), db: Session = Depends(get_db)):
    """Update job spec (for editing in UI); persist to DB and spec.json."""
    job, job_dir = _get_job_and_dir(job_id, db)
    job.spec = body
    spec_path = job_dir / "spec.json"
    spec_path.write_text(json.dumps(body, indent=2))
    db.commit()
    db.refresh(job)
    return {"ok": True, "spec": job.spec}


@router.post("/jobs/{job_id}/regenerate-ac")
def regenerate_acceptance_criteria(job_id: str, db: Session = Depends(get_db)):
    """Re-run AC generation from current spec; merge into spec.user_stories and update job."""
    job, job_dir = _get_job_and_dir(job_id, db)
    spec_path = job_dir / "spec.json"
    if not spec_path.exists():
        raise HTTPException(400, "Spec not found; run pipeline first")
    spec_data = json.loads(spec_path.read_text())
    ac_path = job_dir / "acceptance_criteria.json"
    ac_data = generate_acceptance_criteria(str(spec_path), str(ac_path), job_dir)
    # Merge ACs into spec.user_stories (preserve persona, story_text, tags from spec)
    ac_stories = ac_data.get("user_stories", [])
    if ac_stories:
        spec_user_stories = spec_data.get("user_stories", [])
        for i, spec_us in enumerate(spec_user_stories):
            spec_us_id = spec_us.get("id", f"us-{i+1}")
            matched = False
            for ac_us in ac_stories:
                if ac_us.get("id") == spec_us_id or (i < len(ac_stories) and ac_stories[i].get("id") == ac_us.get("id")):
                    spec_us["acceptance_criteria"] = ac_us.get("acceptance_criteria", [])
                    matched = True
                    break
            if not matched:
                if i < len(ac_stories):
                    spec_us["acceptance_criteria"] = ac_stories[i].get("acceptance_criteria", [])
                else:
                    spec_us["acceptance_criteria"] = []
        spec_data["user_stories"] = spec_user_stories
        spec_path.write_text(json.dumps(spec_data, indent=2))
        job.spec = spec_data
    job.acceptance_criteria = ac_data
    db.commit()
    db.refresh(job)
    return {"ok": True, "acceptance_criteria": ac_data, "spec": job.spec}


@router.get("/jobs/{job_id}/screenshots/{screenshot_id}")
def get_screenshot(job_id: str, screenshot_id: str, db: Session = Depends(get_db)):
    """Serve a screenshot image for evidence display."""
    job, job_dir = _get_job_and_dir(job_id, db)
    screens_dir = job_dir / "screenshots"
    manifest_path = screens_dir / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(404, "Screenshots not found")
    manifest = json.loads(manifest_path.read_text())
    path = None
    for e in manifest:
        if str(e.get("timestamp_ms")) == screenshot_id or e.get("path", "").startswith(screenshot_id):
            path = screens_dir / e.get("path", f"{screenshot_id}.png")
            break
    if path is None:
        path = screens_dir / f"{screenshot_id}.png"
    if not path.exists():
        raise HTTPException(404, "Screenshot not found")
    return FileResponse(path, media_type="image/png")
