#!/usr/bin/env bash
# Test upload flow against local backend. Run from project root.
# Prereqs: backend running on http://127.0.0.1:8000 (cd backend && python3 -m uvicorn app.main:app --port 8000)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
TEST_VIDEO="$ROOT/backend/test_video.mp4"

echo "Testing upload at $BACKEND_URL"

# Health check
if ! curl -sf "$BACKEND_URL/api/health" > /dev/null; then
  echo "Error: Backend not responding at $BACKEND_URL. Start it with: cd backend && python3 -m uvicorn app.main:app --port 8000"
  exit 1
fi

# Create minimal test video if missing
if [ ! -f "$TEST_VIDEO" ]; then
  echo "Creating test video..."
  if ! command -v ffmpeg &>/dev/null; then
    echo "Error: ffmpeg required to create test video. Install ffmpeg or add an existing backend/test_video.mp4"
    exit 1
  fi
  ffmpeg -f lavfi -i color=c=black:s=320x240:d=1 -t 0.5 -c:v libx264 -pix_fmt yuv420p "$TEST_VIDEO" -y -loglevel error
fi

# POST job
RESP=$(curl -sf -X POST -F "video=@$TEST_VIDEO" "$BACKEND_URL/api/jobs")
if ! echo "$RESP" | grep -q '"id"'; then
  echo "Upload failed. Response: $RESP"
  exit 1
fi

JOB_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
if [ -z "$JOB_ID" ]; then
  echo "Could not parse job id from: $RESP"
  exit 1
fi

echo "Upload OK. Job ID: $JOB_ID"

# GET job
GET_RESP=$(curl -sf "$BACKEND_URL/api/jobs/$JOB_ID")
if ! echo "$GET_RESP" | grep -q "\"id\":\"$JOB_ID\""; then
  echo "GET job failed. Response: $GET_RESP"
  exit 1
fi

echo "GET job OK. Status: $(echo "$GET_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)"
echo "All checks passed. Frontend: npm run dev in frontend/ (with NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 in .env.local)"
