#!/usr/bin/env bash
# Test backend locally before deploying to Railway.
# Run from repo root. Backend will start on port 8000 (or PORT).

set -e
cd "$(dirname "$0")/.."

echo "Testing backend locally (Railway uses same app with Root Directory = backend)"
echo ""

# Start backend in background
cd backend
echo "Starting uvicorn on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!
cd ..

# Wait for server to be up
for i in {1..15}; do
  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health | grep -q 200; then
    echo "Backend is up."
    break
  fi
  if [ "$i" -eq 15 ]; then
    kill $UVICORN_PID 2>/dev/null || true
    echo "Backend failed to respond on /api/health"
    exit 1
  fi
  sleep 1
done

echo ""
echo "GET /api/health:"
curl -s http://127.0.0.1:8000/api/health
echo ""
echo ""
echo "GET /api/jobs (list):"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8000/api/jobs
echo ""
echo "Stopping backend (PID $UVICORN_PID)..."
kill $UVICORN_PID 2>/dev/null || true
echo "Done. Backend is ready for Railway deploy (set Root Directory = backend)."
