"""Structured product spec JSON schema for LLM output."""
from typing import Any

EVIDENCE_REF = {"timestamp": float, "transcript_excerpt": str, "screenshot_id": str}

SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "feature_summary": {"type": "string"},
        "actors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "object"}},
                },
            },
        },
        "user_stories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "persona": {"type": ["string", "array"]},
                    "story_text": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "object"}},
                    "acceptance_criteria": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "given": {"type": "string"},
                                "when": {"type": "string"},
                                "then": {"type": "string"},
                                "and": {"type": "array", "items": {"type": "string"}},
                                "evidence_refs": {"type": "array", "items": {"type": "object"}},
                            },
                        },
                    },
                },
            },
        },
        "workflows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "evidence_refs": {"type": "array", "items": {"type": "object"}},
                },
            },
        },
        "business_rules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "object"}},
                },
            },
        },
        "permissions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "object"}},
                },
            },
        },
        "open_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["feature_summary", "user_stories", "open_questions"],
}

SPEC_REPAIR_PROMPT = """Fix the following JSON so it conforms to this schema. Return only valid JSON.
Schema: the object must have keys: feature_summary (string), actors (array), user_stories (array), workflows (array), business_rules (array), permissions (array), open_questions (array). 
Each user_story must have: id, title, persona (string or array), story_text (string in "As a / I need / So that" format), tags (optional array), evidence_refs (array). 
Any requirement object should have evidence_refs: array of { timestamp, transcript_excerpt, screenshot_id }. Use empty arrays/strings for missing optional fields."""


def validate_and_repair_spec(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure required keys exist; coerce types; return valid subset."""
    out = {
        "feature_summary": data.get("feature_summary") or "",
        "actors": data.get("actors") or [],
        "user_stories": data.get("user_stories") or [],
        "workflows": data.get("workflows") or [],
        "business_rules": data.get("business_rules") or [],
        "permissions": data.get("permissions") or [],
        "open_questions": data.get("open_questions") or [],
    }
    for item in out["user_stories"]:
        if isinstance(item, dict):
            if "evidence_refs" not in item:
                item["evidence_refs"] = []
            if "acceptance_criteria" not in item:
                item["acceptance_criteria"] = []
            if "persona" not in item:
                item["persona"] = ""
            if "story_text" not in item:
                item["story_text"] = ""
            if "tags" not in item:
                item["tags"] = []
            # Ensure each AC has required fields
            for ac in item.get("acceptance_criteria", []):
                if isinstance(ac, dict):
                    if "and" not in ac:
                        ac["and"] = []
                    if "evidence_refs" not in ac:
                        ac["evidence_refs"] = []
    for item in out.get("workflows", []) or []:
        if isinstance(item, dict) and "evidence_refs" not in item:
            item["evidence_refs"] = []
    for item in out.get("business_rules", []) or []:
        if isinstance(item, dict) and "evidence_refs" not in item:
            item["evidence_refs"] = []
    for item in out.get("permissions", []) or []:
        if isinstance(item, dict) and "evidence_refs" not in item:
            item["evidence_refs"] = []
    return out
