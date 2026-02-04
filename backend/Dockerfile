# Backend for Railway (or Cloud Run) - Python 3.11 + ffmpeg + FastAPI
# Use Dockerfile to avoid Nixpacks libstdc++.so.6 issue with numpy/opencv
FROM python:3.11-slim-bookworm

# ffmpeg + OpenCV/numpy runtime deps (libstdc++ fixes "libstdc++.so.6: cannot open shared object")
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

ENV PORT=8000
ENV STORAGE_ROOT=/tmp/storage
EXPOSE 8000

# Railway sets PORT at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
