# Backend for Cloud Run (Firebase) - Python 3.11 + ffmpeg + FastAPI
FROM python:3.11-slim-bookworm

# Install ffmpeg (required for video processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Cloud Run: only /tmp is writable; use Supabase/Postgres for DB
ENV PORT=8080
ENV STORAGE_ROOT=/tmp/storage
EXPOSE 8080

# Run with uvicorn; use 0.0.0.0 so Cloud Run can reach it
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
