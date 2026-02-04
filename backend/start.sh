#!/bin/bash
set -e

# Find and set LD_LIBRARY_PATH for libstdc++ (only if found)
LIB_FILE=$(find /nix/store -name libstdc++.so.6 -type f 2>/dev/null | head -1)
if [ -n "$LIB_FILE" ]; then
  export LD_LIBRARY_PATH="$(dirname "$LIB_FILE"):${LD_LIBRARY_PATH}"
fi

# When Root Directory = backend, app is at /app. When built from repo root, app is at /app/backend.
if [ -d /app/backend ]; then
  cd /app/backend
else
  cd /app
fi
exec /app/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
