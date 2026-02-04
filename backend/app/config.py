"""App configuration."""
import logging
import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Project root: backend/app/config.py -> backend -> project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

logger = logging.getLogger("app.config")


def _mask_key(k: str | None) -> str:
    if not k or len(k) < 12:
        return "(none or too short)"
    return f"{k[:10]}...{k[-4:]}(len={len(k)})"


class Settings(BaseSettings):
    storage_root: Path = Path(os.getenv("STORAGE_ROOT", str(_PROJECT_ROOT / "storage"))).resolve()
    max_upload_mb: int = 500
    allowed_video_types: set[str] = {"video/mp4", "video/webm"}
    openai_api_key: str | None = None
    openai_org_id: str | None = None  # optional; for multi-org or project keys
    openai_project_id: str | None = None  # optional; required for sk-proj- project keys
    redis_url: str | None = os.getenv("REDIS_URL")  # optional for ARQ

    class Config:
        env_file = str(_ENV_PATH)
        env_file_encoding = "utf-8"
        extra = "ignore"


# Load .env into os.environ first so it's definitely available (pydantic also reads env)
if _ENV_PATH.exists():
    from dotenv import load_dotenv
    load_dotenv(_ENV_PATH, override=True)

settings = Settings()

# Re-read from env if pydantic didn't get it (e.g. env_file path issue)
_env_key = os.getenv("OPENAI_API_KEY")
if not settings.openai_api_key and _env_key:
    settings.openai_api_key = _env_key.strip() if isinstance(_env_key, str) else None
# Always strip to remove any \r, trailing newline, or spaces from .env
if settings.openai_api_key:
    settings.openai_api_key = settings.openai_api_key.strip()
# Don't pass project/org to the client (api_key only). Unset so OpenAI client doesn't read them from env.
os.environ.pop("OPENAI_PROJECT_ID", None)
os.environ.pop("OPENAI_ORG_ID", None)


def openai_client_kwargs() -> dict:
    """Kwargs for OpenAI(): api_key only (no project/org header)."""
    if not settings.openai_api_key:
        return {}
    return {"api_key": settings.openai_api_key}


logger.info(
    "config loaded: env_file=%s exists=%s key=%s",
    _ENV_PATH,
    _ENV_PATH.exists(),
    _mask_key(settings.openai_api_key),
)
