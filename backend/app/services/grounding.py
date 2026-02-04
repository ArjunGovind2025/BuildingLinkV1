"""Grounding: align transcript segments to screenshots by timestamp; produce grounded chunks."""
import json
from pathlib import Path


def build_grounded_chunks(job_dir: Path, grounded_path: str) -> None:
    """Produce grounded_chunks.json: each item has timestamp_ms, screenshot_id, screenshot_path, vision_summary, transcript_excerpt."""
    manifest_path = job_dir / "screenshots" / "manifest.json"
    transcript_path = job_dir / "transcript.json"
    cache_dir = job_dir / "cache" / "vision"
    screenshots_dir = job_dir / "screenshots"

    if not manifest_path.exists() or not transcript_path.exists():
        Path(grounded_path).write_text(json.dumps([]))
        return

    manifest = json.loads(manifest_path.read_text())
    transcript_data = json.loads(transcript_path.read_text())
    segments = transcript_data.get("segments", [])

    chunks = []
    for entry in manifest:
        ts_ms = entry.get("timestamp_ms", 0)
        path = entry.get("path", "")
        screenshot_id = str(ts_ms)
        ts_sec = ts_ms / 1000.0

        # Transcript excerpt: segments that overlap [ts_sec - 0.5, ts_sec + 0.5] or contain ts_sec
        excerpt_parts = []
        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            if start <= ts_sec <= end or (start <= ts_sec + 0.5 and end >= ts_sec - 0.5):
                excerpt_parts.append(seg.get("text", "").strip())
        transcript_excerpt = " ".join(excerpt_parts).strip()

        # Nearest segment if no overlap
        if not transcript_excerpt and segments:
            best = min(segments, key=lambda s: min(abs(s.get("start", 0) - ts_sec), abs(s.get("end", 0) - ts_sec)))
            transcript_excerpt = best.get("text", "").strip()

        vision_summary = {}
        cache_file = cache_dir / f"{Path(path).stem}.json"
        if cache_file.exists():
            vision_summary = json.loads(cache_file.read_text())

        chunks.append({
            "timestamp_ms": ts_ms,
            "screenshot_id": screenshot_id,
            "screenshot_path": path,
            "vision_summary": vision_summary,
            "transcript_excerpt": transcript_excerpt,
        })

    Path(grounded_path).write_text(json.dumps(chunks, indent=2))
