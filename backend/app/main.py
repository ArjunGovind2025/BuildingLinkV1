"""FastAPI app: CORS, routes, startup."""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Add new columns to existing jobs table if missing (SQLite)
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(export.router, prefix="/api", tags=["export"])
