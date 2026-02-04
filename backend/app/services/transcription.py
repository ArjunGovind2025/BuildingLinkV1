"""Speech transcription: call OpenAI Whisper, normalize to timestamped segments."""
import json
import logging
from pathlib import Path
from openai import OpenAI

from app.config import settings, openai_client_kwargs

logger = logging.getLogger("app.transcription")


def _mask_key(k: str | None) -> str:
    if not k or len(k) < 12:
        return "(none or too short)"
    return f"{k[:10]}...{k[-4:]}(len={len(k)})"


def transcribe_audio(audio_path: str, transcript_path: str) -> None:
    """Transcribe audio to timestamped segments; save to transcript.json."""
    kwargs = openai_client_kwargs()
    if not kwargs.get("api_key"):
        raise ValueError("OPENAI_API_KEY is not set; check .env and restart backend")
    logger.info("transcribe_audio: key=%s", _mask_key(kwargs.get("api_key")))
    client = OpenAI(**kwargs)
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    segments = []
    if hasattr(transcript, "segments") and transcript.segments:
        for s in transcript.segments:
            segments.append({
                "start": float(getattr(s, "start", 0)),
                "end": float(getattr(s, "end", 0)),
                "text": getattr(s, "text", "").strip(),
            })
    else:
        text = getattr(transcript, "text", "") or ""
        if text:
            segments.append({"start": 0.0, "end": 0.0, "text": text})
    out = {"segments": segments}
    Path(transcript_path).write_text(json.dumps(out, indent=2))
