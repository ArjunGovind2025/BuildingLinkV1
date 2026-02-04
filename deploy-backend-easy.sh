#!/bin/bash

echo "🚀 Easiest Backend Deployment - Railway"
echo "========================================"
echo ""
echo "Option 1: Web Interface (Easiest - No CLI needed)"
echo "-------------------------------------------------"
echo "1. Go to: https://railway.app"
echo "2. Sign up/Login (free account)"
echo "3. Click 'New Project' → 'Deploy from GitHub repo'"
echo "4. Select repository: ArjunGovind2025/BuildingLinkV1"
echo "5. After it deploys, click on the service"
echo "6. Go to 'Variables' tab and add:"
echo "   - OPENAI_API_KEY = $(grep OPENAI_API_KEY .env | cut -d'=' -f2)"
echo "   - OPENAI_PROJECT_ID = $(grep OPENAI_PROJECT_ID .env | cut -d'=' -f2)"
echo "7. Go to 'Settings' → 'Root Directory' → Set to: backend"
echo "8. Go to 'Settings' → 'Generate Domain' → Copy the URL"
echo ""
echo "That's it! Your backend will be live in ~2 minutes."
echo ""
read -p "Press Enter to continue to Option 2 (CLI method) or Ctrl+C to exit..."

echo ""
echo "Option 2: CLI Method (Faster if already logged in)"
echo "--------------------------------------------------"
echo ""

# Check if logged in
if railway whoami &>/dev/null; then
    echo "✅ Already logged into Railway!"
    echo ""
    echo "Deploying backend..."
    cd backend
    
    # Check if already linked
    if [ ! -f ".railway/railway.toml" ]; then
        echo "Creating new Railway project..."
        railway init --name buildinglink-backend
    fi
    
    # Set environment variables
    echo "Setting environment variables..."
    railway variables set OPENAI_API_KEY="$(grep OPENAI_API_KEY ../.env | cut -d'=' -f2)"
    railway variables set OPENAI_PROJECT_ID="$(grep OPENAI_PROJECT_ID ../.env | cut -d'=' -f2)"
    
    # Deploy
    echo "Deploying..."
    railway up --detach
    
    # Get URL
    sleep 5
    BACKEND_URL=$(railway domain 2>/dev/null || railway status --json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('service', {}).get('domain', '') or '')" 2>/dev/null || echo "")
    
    if [ -n "$BACKEND_URL" ]; then
        echo ""
        echo "✅ Backend deployed!"
        echo "Backend URL: $BACKEND_URL"
        echo ""
        echo "Update your frontend with:"
        echo "./fix-backend-url.sh $BACKEND_URL"
    else
        echo ""
        echo "⚠️  Deployment started. Get your URL from Railway dashboard:"
        echo "https://railway.app"
    fi
else
    echo "❌ Not logged into Railway."
    echo ""
    echo "Quick login:"
    echo "1. Run: railway login"
    echo "2. Complete authentication in browser"
    echo "3. Run this script again"
    echo ""
    echo "Or use Option 1 (Web Interface) above - it's easier!"
fi
