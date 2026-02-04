#!/bin/bash
set -e

# Find and set LD_LIBRARY_PATH for libstdc++ (only if found)
LIB_FILE=$(find /nix/store -name libstdc++.so.6 -type f 2>/dev/null | head -1)
if [ -n "$LIB_FILE" ]; then
  export LD_LIBRARY_PATH="$(dirname "$LIB_FILE"):${LD_LIBRARY_PATH}"
fi

# Change to backend directory
cd /app/backend

# Start the application
exec /app/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
