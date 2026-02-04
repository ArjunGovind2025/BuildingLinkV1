"""Intermediate spec extraction: LLM converts grounded chunks to structured spec with evidence_refs."""
import json
from pathlib import Path
from openai import OpenAI

from app.config import settings, openai_client_kwargs
from app.schemas.spec_schema import validate_and_repair_spec, SPEC_REPAIR_PROMPT


def _full_transcript_text(transcript_path: str | Path) -> str:
    """Build full transcript as continuous text with timestamps (primary source)."""
    path = Path(transcript_path)
    if not path.exists():
        return ""
    data = json.loads(path.read_text())
    segments = data.get("segments", [])
    lines = []
    for s in segments:
        start = s.get("start", 0)
        end = s.get("end", 0)
        text = (s.get("text", "") or "").strip()
        if text:
            lines.append(f"[{start:.1f}s - {end:.1f}s] {text}")
    return "\n".join(lines)


def _build_context(grounded_path: str, transcript_path: str | Path | None = None, max_chars: int = 200000) -> str:
    parts = []
    # Full transcript first (primary source) so nothing is missed
    if transcript_path and Path(transcript_path).exists():
        full = _full_transcript_text(transcript_path)
        if full:
            parts.append("## Full transcript (PRIMARY SOURCE – extract exhaustively from this)\n" + full)
    # Then grounded evidence (transcript excerpts + vision per screenshot)
    data = json.loads(Path(grounded_path).read_text())
    evidence_parts = []
    n = len(parts[0]) if parts else 0
    for chunk in data:
        ts = chunk.get("timestamp_ms", 0)
        sid = chunk.get("screenshot_id", "")
        excerpt = chunk.get("transcript_excerpt", "")
        vision = chunk.get("vision_summary", {})
        block = f"[{ts}ms screenshot={sid}]\nTranscript: {excerpt}\nVision: {json.dumps(vision)}"
        n += len(block)
        if n > max_chars:
            break
        evidence_parts.append(block)
    if evidence_parts:
        parts.append("## Evidence (transcript + vision per screenshot)\n" + "\n\n".join(evidence_parts))
    return "\n\n".join(parts)


EXTRACTION_PROMPT = """You are given a FULL TRANSCRIPT (primary source) and evidence chunks from a narrated screen recording. Your job is to extract an EXHAUSTIVE structured product spec.

PRIORITY: The transcript is the PRIMARY source. Extract EVERY requirement, user story, workflow step, validation, edge case, and business rule the narrator mentioned. Do not omit scenarios or steps they described. Use vision/screenshots only to ground and supplement.

Rules:
- Be EXHAUSTIVE: include every requirement mentioned in the transcript. Do not skip validations, error cases, or flows the user described.
- Every requirement MUST have evidence_refs: array of { "timestamp": number (ms), "transcript_excerpt": string, "screenshot_id": string }. Use timestamp_ms and screenshot_id from the evidence chunks where the requirement appears.
- Only put in open_questions what is genuinely unclear or unsupported. Do not put transcript content there just because it was brief.
- Output valid JSON only, with keys: feature_summary, actors, user_stories, workflows, business_rules, permissions, open_questions.
- user_stories: array of { id, title, persona (string or array of strings), story_text (As a / I need / So that format), tags (optional array), evidence_refs } – one per distinct capability/feature the user described.
  * persona: Who is this story for? (e.g., "Manager", "Security Officer", or ["Manager", "Security Officer"])
  * story_text: Full story statement in format "As a [persona] / I need [capability] / So that [benefit]"
  * title: Concise title for the story
- workflows: array of { name, steps (array of strings), evidence_refs } – include every flow and step sequence mentioned.
- business_rules: array of { description, evidence_refs } – validations, constraints, edge cases.
- permissions: array of { description, evidence_refs }.
- actors: array of { name, role, evidence_refs }.
Return only the JSON object, no markdown."""


def extract_spec(grounded_path: str, spec_path: str, transcript_path: str | Path | None = None) -> dict:
    """Call LLM with full transcript (primary) + grounded chunks; parse and repair JSON; save to spec_path; return spec dict."""
    context = _build_context(grounded_path, transcript_path=transcript_path)
    client = OpenAI(**openai_client_kwargs())
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You output only valid JSON. Extract exhaustively from the transcript."},
            {"role": "user", "content": f"{EXTRACTION_PROMPT}\n\n{context}"},
        ],
        max_tokens=8192,
    )
    text = (resp.choices[0].message.content or "{}").strip()
    if text.startswith("```"):
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        repair_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"{SPEC_REPAIR_PROMPT}\n\nInvalid JSON:\n{text}"},
            ],
            max_tokens=8192,
        )
        repair_text = (repair_resp.choices[0].message.content or "{}").strip()
        if repair_text.startswith("```"):
            start = repair_text.find("{")
            end = repair_text.rfind("}") + 1
            if start >= 0 and end > start:
                repair_text = repair_text[start:end]
        try:
            data = json.loads(repair_text)
        except json.JSONDecodeError:
            data = {"feature_summary": "", "user_stories": [], "open_questions": ["Failed to parse spec"]}
    data = validate_and_repair_spec(data)
    Path(spec_path).write_text(json.dumps(data, indent=2))
    return data
