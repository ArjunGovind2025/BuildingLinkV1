"""Acceptance criteria generation: convert spec to GIVEN/WHEN/THEN with evidence_refs."""
import json
from pathlib import Path
from openai import OpenAI

from app.config import settings, openai_client_kwargs

AC_SCHEMA_KEYS = ("id", "given", "when", "then", "and", "evidence_refs")
AC_REPAIR_PROMPT = """Fix the following JSON. It must be an object with key "user_stories" which is an array. Each user story must have: id, title, persona (string or array), story_text (string), acceptance_criteria (array). Each acceptance criterion must have: id (local numbering like AC1, AC2 per story), given, when, then, and (optional array of strings), evidence_refs (array of { timestamp, transcript_excerpt, screenshot_id }). Each story must have at least 1 acceptance criterion. Return only valid JSON."""


def _validate_ac_item(item: dict) -> dict:
    return {
        "id": str(item.get("id", "")),
        "given": str(item.get("given", "")),
        "when": str(item.get("when", "")),
        "then": str(item.get("then", "")),
        "and": item.get("and") if isinstance(item.get("and"), list) else [],
        "evidence_refs": item.get("evidence_refs") if isinstance(item.get("evidence_refs"), list) else [],
    }


def _full_transcript_text(transcript_path: Path) -> str:
    """Build full transcript as continuous text (primary source for AC)."""
    if not transcript_path.exists():
        return ""
    data = json.loads(transcript_path.read_text())
    segments = data.get("segments", [])
    lines = []
    for s in segments:
        start = s.get("start", 0)
        end = s.get("end", 0)
        text = (s.get("text", "") or "").strip()
        if text:
            lines.append(f"[{start:.1f}s - {end:.1f}s] {text}")
    return "\n".join(lines)


def generate_acceptance_criteria(spec_path: str, ac_path: str, job_dir: Path) -> dict:
    """Generate acceptance criteria nested under each user story in GIVEN/WHEN/THEN/AND format; attach evidence_refs; save and return."""
    spec_data = json.loads(Path(spec_path).read_text())
    transcript_path = job_dir / "transcript.json"
    full_transcript = _full_transcript_text(transcript_path)
    client = OpenAI(**openai_client_kwargs())
    
    user_stories = spec_data.get("user_stories", [])
    if not user_stories:
        # Fallback: return empty structure
        out = {"user_stories": []}
        Path(ac_path).write_text(json.dumps(out, indent=2))
        return out
    
    prompt = f"""Generate EXHAUSTIVE acceptance criteria in GIVEN / WHEN / THEN / AND format, nested under each user story.

PRIORITY: The transcript below is the PRIMARY source. For EACH user story, generate MULTIPLE acceptance criteria covering every scenario, validation, edge case, and flow the narrator described for that story. Do not skip steps or cases they mentioned.

CRITICAL RULES:
- For EACH user story, generate MULTIPLE acceptance criteria (at least 1 per story, typically 2-5, more if the transcript describes many scenarios).
- Each user story MUST have at least 1 acceptance criterion.
- Be EXHAUSTIVE: convert every requirement/scenario/validation mentioned in the transcript for each story into GIVEN/WHEN/THEN/AND criteria.
- Format: GIVEN (precondition), WHEN (action/trigger), THEN (expected outcome), AND (optional: additional outcomes/validations as array of strings).
- Every criterion MUST include all three: GIVEN, WHEN, and THEN. AND is optional.
- Every criterion MUST have evidence_refs: array of {{ "timestamp": number (ms), "transcript_excerpt": string, "screenshot_id": string }}. Use evidence_refs from the user story; if missing, use timestamps/excerpts from the transcript.
- Output valid JSON only: {{ "user_stories": [ {{ "id": "us-1", "title": "...", "persona": "...", "story_text": "...", "acceptance_criteria": [ {{ "id": "AC1", "given": "...", "when": "...", "then": "...", "and": ["..."], "evidence_refs": [...] }}, {{ "id": "AC2", ... }}, ... ] }}, ... ] }}
- Each user story should have its own acceptance_criteria array.
- AC numbering is LOCAL to each story: Start with "AC1" for the first AC in each story, then "AC2", "AC3", etc. Do NOT use global numbering.
- Do NOT reference ACs across stories. Each story's ACs are independent.
- Preserve Jira-style looseness inside ACs (flexible wording), but be strict about structure (GIVEN/WHEN/THEN required).

## Full transcript (PRIMARY SOURCE – derive criteria from this)
{full_transcript}

## User stories (generate ACs for each)
{json.dumps(user_stories, indent=2)}"""

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You output only valid JSON with key user_stories. Each user story must have an acceptance_criteria array. Generate exhaustive acceptance criteria from the transcript for each story."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=16384,
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
            messages=[{"role": "user", "content": f"{AC_REPAIR_PROMPT}\n\n{text}"}],
            max_tokens=16384,
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
            data = {"user_stories": []}
    
    # Validate and repair: ensure each user story has acceptance_criteria array with at least 1 AC
    validated_stories = []
    for us in data.get("user_stories", []):
        if not isinstance(us, dict):
            continue
        acs = us.get("acceptance_criteria", [])
        if not isinstance(acs, list):
            acs = []
        validated_ac = []
        for i, ac in enumerate(acs):
            if not isinstance(ac, dict):
                continue
            v = _validate_ac_item(ac)
            # Number ACs locally per story: AC1, AC2, AC3, etc.
            if not v.get("id"):
                v["id"] = f"AC{i+1}"
            # Ensure AC has required fields (GIVEN, WHEN, THEN)
            if not v.get("given") or not v.get("when") or not v.get("then"):
                continue  # Skip invalid ACs
            validated_ac.append(v)
        # Ensure each story has at least 1 AC
        if len(validated_ac) == 0:
            # Skip stories without valid ACs (or could generate a placeholder, but skip for now)
            continue
        us_copy = {k: v for k, v in us.items() if k != "acceptance_criteria"}
        us_copy["acceptance_criteria"] = validated_ac
        validated_stories.append(us_copy)
    
    out = {"user_stories": validated_stories}
    Path(ac_path).write_text(json.dumps(out, indent=2))
    return out
