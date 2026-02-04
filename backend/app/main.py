"""FastAPI app: CORS, routes, startup."""
import logging
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from app.database import engine, Base
from app.config import settings
from app.api import jobs, export

# Ensure config/key diagnostics are visible in console
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s %(levelname)s %(message)s",
    stream=sys.stdout,
    force=True,
)
logging.getLogger("app").setLevel(logging.INFO)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Add new columns to existing jobs table if missing (SQLite only; Postgres uses create_all)
    if "sqlite" in str(engine.url):
        for col in ("transcript_segments", "screenshots_captured", "screenshots_analyzed"):
            try:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col} INTEGER"))
                    conn.commit()
            except Exception:
                pass  # column already exists
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    (settings.storage_root / "jobs").mkdir(parents=True, exist_ok=True)
    yield
    # shutdown if needed


app = FastAPI(title="Video to Acceptance Criteria", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request so we can see if uploads reach the backend and when they fail."""
    cl = request.headers.get("content-length", "?")
    logger.info("request start method=%s path=%s content_length=%s", request.method, request.url.path, cl)
    start = time.monotonic()
    try:
        response = await call_next(request)
        elapsed = time.monotonic() - start
        logger.info("request done method=%s path=%s status=%s elapsed=%.2fs", request.method, request.url.path, response.status_code, elapsed)
        return response
    except Exception as e:
        elapsed = time.monotonic() - start
        logger.exception("request failed method=%s path=%s elapsed=%.2fs error=%s", request.method, request.url.path, elapsed, e)
        raise


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/api/health")
def health():
    """Simple health check so we can verify the backend is reachable (e.g. from browser or curl)."""
    return {"status": "ok"}


app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(export.router, prefix="/api", tags=["export"])
