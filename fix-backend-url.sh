#!/bin/bash
# Set backend URL and build frontend (for Vercel or local). No Firebase deploy.

echo "🔧 Set Backend URL & Build Frontend"
echo "===================================="
echo ""

if [ -z "$1" ]; then
    echo "Usage: $0 <BACKEND_URL>"
    echo "  e.g. $0 https://your-app.up.railway.app"
    echo ""
    read -p "Enter your backend URL: " BACKEND_URL
else
    BACKEND_URL="$1"
fi

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend URL is required!"
    exit 1
fi

BACKEND_URL="${BACKEND_URL%/}"
echo "Using backend URL: $BACKEND_URL"
echo ""

echo "Testing backend..."
if curl -s "$BACKEND_URL/api/health" | grep -q '"status":"ok"'; then
    echo "✅ Backend is reachable"
else
    echo "⚠️  Could not reach $BACKEND_URL/api/health — continuing anyway."
fi
echo ""

echo "Building frontend with NEXT_PUBLIC_BACKEND_URL=$BACKEND_URL"
cd frontend
NEXT_PUBLIC_BACKEND_URL="$BACKEND_URL" npm run build
code=$?
cd ..
if [ $code -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi
echo "✅ Build successful. Deploy the frontend (e.g. Vercel) with NEXT_PUBLIC_BACKEND_URL=$BACKEND_URL"
