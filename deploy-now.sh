#!/bin/bash

set -e

echo "🚀 Starting Deployment Process"
echo "=============================="
echo ""

# Check if logged into Railway
echo "Checking Railway authentication..."
if ! railway whoami &>/dev/null; then
    echo "❌ Not logged into Railway. Please run: railway login"
    echo "   This will open a browser for authentication."
    exit 1
fi

# Check if logged into Vercel
echo "Checking Vercel authentication..."
if ! vercel whoami &>/dev/null; then
    echo "❌ Not logged into Vercel. Please run: vercel login"
    echo "   This will open a browser for authentication."
    exit 1
fi

echo "✅ Both Railway and Vercel are authenticated!"
echo ""

# Deploy Backend to Railway
echo "📦 Step 1: Deploying Backend to Railway"
echo "----------------------------------------"
cd backend

# Check if already linked to a Railway project
if [ ! -f ".railway/railway.toml" ]; then
    echo "Creating new Railway project..."
    railway init --name buildinglink-backend
else
    echo "Using existing Railway project..."
fi

# Set environment variables (user will need to add OPENAI_API_KEY)
echo ""
echo "⚠️  IMPORTANT: Add your OPENAI_API_KEY environment variable:"
echo "   railway variables set OPENAI_API_KEY=your-key-here"
echo ""
read -p "Have you set OPENAI_API_KEY? (y/n): " has_key

if [ "$has_key" != "y" ]; then
    echo "Please set OPENAI_API_KEY first, then run this script again."
    exit 1
fi

# Deploy
echo "Deploying backend..."
railway up --detach

# Get the backend URL
echo "Getting backend URL..."
BACKEND_URL=$(railway domain 2>/dev/null || railway status --json | grep -o '"domain":"[^"]*' | cut -d'"' -f4 || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo "⚠️  Could not automatically get backend URL."
    echo "   Please get it from Railway dashboard and set it manually."
    read -p "Enter your Railway backend URL (e.g., https://xxx.up.railway.app): " BACKEND_URL
fi

echo "✅ Backend deployed at: $BACKEND_URL"
echo ""

# Deploy Frontend to Vercel
echo "📦 Step 2: Deploying Frontend to Vercel"
echo "----------------------------------------"
cd ../frontend

# Link to Vercel project
if [ ! -f ".vercel/project.json" ]; then
    echo "Linking to Vercel project..."
    vercel link --yes
fi

# Set environment variable
echo "Setting NEXT_PUBLIC_BACKEND_URL=$BACKEND_URL"
vercel env add NEXT_PUBLIC_BACKEND_URL production <<< "$BACKEND_URL" || \
    vercel env rm NEXT_PUBLIC_BACKEND_URL production --yes && \
    vercel env add NEXT_PUBLIC_BACKEND_URL production <<< "$BACKEND_URL"

# Deploy
echo "Deploying frontend..."
FRONTEND_URL=$(vercel --prod --yes)

echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo "Backend URL:  $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "Your app is now live! 🎉"
