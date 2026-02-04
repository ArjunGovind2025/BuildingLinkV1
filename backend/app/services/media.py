"""Media preprocessing: extract audio, frame diff, screenshot capture."""
import shutil
import subprocess
from pathlib import Path

import cv2

# Tunable
DIFF_THRESHOLD = 0.035  # normalized MAD above this = meaningful change (lower = more sensitive)
MIN_INTERVAL_MS = 1000  # min ms between screenshots (1s)
MAX_INTERVAL_MS = 30000  # force capture at least every 30s even if diff is small
RESIZE_WIDTH = 320
RESIZE_HEIGHT = 180

FFMPEG_MSG = (
    "ffmpeg is not installed or not on PATH. "
    "Install it: https://ffmpeg.org/download.html "
    "(e.g. on macOS: brew install ffmpeg)"
)


def _get_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise FileNotFoundError(FFMPEG_MSG)
    return path


def extract_audio(video_path: str, audio_path: str) -> None:
    """Extract audio to WAV using ffmpeg."""
    ffmpeg = _get_ffmpeg()
    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                video_path,
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                audio_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise FileNotFoundError(FFMPEG_MSG)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "") if isinstance(e.stderr, str) else (e.stderr.decode("utf-8", errors="replace") if e.stderr else "")
        raise RuntimeError(f"ffmpeg failed: {stderr.strip() or e}")


def capture_screenshots(video_path: str, screenshots_dir: str) -> None:
    """Decode video, compute pixel diff between consecutive frames, capture screenshot on meaningful change."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    manifest = []
    prev_gray = None
    last_capture_ms = -MIN_INTERVAL_MS - 1
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        timestamp_ms = int((frame_index / fps) * 1000)
        small = cv2.resize(frame, (RESIZE_WIDTH, RESIZE_HEIGHT))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            mad = diff.mean() / 255.0
            time_since_last = timestamp_ms - last_capture_ms
            meaningful_change = mad >= DIFF_THRESHOLD and time_since_last >= MIN_INTERVAL_MS
            # Force capture periodically so we don't miss slow or subtle changes
            overdue = time_since_last >= MAX_INTERVAL_MS
            if meaningful_change or overdue:
                path = f"{timestamp_ms}.png"
                out_path = Path(screenshots_dir) / path
                cv2.imwrite(str(out_path), frame)
                manifest.append({"timestamp_ms": timestamp_ms, "path": path})
                last_capture_ms = timestamp_ms
        else:
            path = f"{timestamp_ms}.png"
            out_path = Path(screenshots_dir) / path
            cv2.imwrite(str(out_path), frame)
            manifest.append({"timestamp_ms": timestamp_ms, "path": path})
            last_capture_ms = timestamp_ms
        prev_gray = gray
        frame_index += 1

    cap.release()
    manifest_path = Path(screenshots_dir) / "manifest.json"
    import json
    manifest_path.write_text(json.dumps(manifest, indent=2))
