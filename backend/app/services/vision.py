"""Visual understanding: per-screenshot vision API + cache."""
import json
import base64
from pathlib import Path
from openai import OpenAI

from app.config import settings, openai_client_kwargs

VISION_SCHEMA_KEYS = ("page", "elements", "errors_or_banners", "empty_states", "navigation_context")
PROMPT = """Describe this UI screenshot in JSON with exactly these keys (use empty array/string if none):
- page: string (page or section name)
- elements: array of strings (visible UI elements: buttons, inputs, tabs, modals, links)
- errors_or_banners: array of strings (errors, banners, toasts)
- empty_states: string (describe any empty state)
- navigation_context: string (breadcrumb or where we are in the app)

Return only valid JSON, no markdown."""


def _encode_image(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def _repair_vision_response(data: dict) -> dict:
    out = {}
    for k in VISION_SCHEMA_KEYS:
        v = data.get(k)
        if k == "page" and not isinstance(v, str):
            out[k] = str(v) if v is not None else ""
        elif k in ("elements", "errors_or_banners") and not isinstance(v, list):
            out[k] = list(v) if isinstance(v, (list, tuple)) else ([v] if v is not None else [])
        elif k in ("empty_states", "navigation_context"):
            out[k] = str(v) if v is not None else ""
        else:
            out[k] = v
    return out


def describe_screenshots(job_dir: Path) -> None:
    """For each screenshot in manifest, call vision API (or use cache), save to cache/vision/{basename}.json."""
    manifest_path = job_dir / "screenshots" / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text())
    cache_dir = job_dir / "cache" / "vision"
    cache_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(**openai_client_kwargs())
    screenshots_dir = job_dir / "screenshots"

    for entry in manifest:
        path = entry.get("path", "")
        basename = Path(path).stem
        cache_file = cache_dir / f"{basename}.json"
        if cache_file.exists():
            continue
        img_path = screenshots_dir / path
        if not img_path.exists():
            continue
        b64 = _encode_image(img_path)
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    }
                ],
                max_tokens=1024,
            )
            text = resp.choices[0].message.content or "{}"
            text = text.strip()
            if text.startswith("```"):
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    text = text[start:end]
            data = json.loads(text)
            data = _repair_vision_response(data)
        except Exception:
            data = {k: "" if k in ("page", "empty_states", "navigation_context") else [] for k in VISION_SCHEMA_KEYS}
        cache_file.write_text(json.dumps(data, indent=2))
