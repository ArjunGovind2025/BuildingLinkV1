#!/bin/bash
set -e

# Find and set LD_LIBRARY_PATH for libstdc++
LIB_PATH=$(find /nix/store -name libstdc++.so.6 -type f 2>/dev/null | head -1 | xargs dirname)
export LD_LIBRARY_PATH="${LIB_PATH}:${LD_LIBRARY_PATH}"

# Change to backend directory
cd /app/backend

# Start the application
exec /app/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
