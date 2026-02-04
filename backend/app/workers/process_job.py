"""Background pipeline runner. Runs full pipeline in a thread (no Redis required for MVP)."""
import threading
from app.workers.pipeline import process_job


def run_pipeline_background(job_id: str) -> None:
    thread = threading.Thread(target=process_job, args=(job_id,), daemon=True)
    thread.start()
