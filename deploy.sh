#!/bin/bash

# Quick deployment helper script
# This script helps you deploy your app step by step

echo "🚀 Video to Acceptance Criteria - Deployment Helper"
echo "=================================================="
echo ""
echo "This script will guide you through deployment."
echo ""
echo "Choose your deployment method:"
echo "1. Deploy to Vercel (Frontend) + Railway (Backend) - Recommended"
echo "2. Deploy to Vercel (Frontend) + Render (Backend)"
echo "3. Quick test with ngrok (Local development with public URLs)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
  1)
    echo ""
    echo "📦 Deploying to Railway + Vercel"
    echo ""
    echo "Step 1: Deploy Backend to Railway"
    echo "----------------------------------"
    echo "1. Go to https://railway.app and sign up/login"
    echo "2. Click 'New Project' → 'Deploy from GitHub repo'"
    echo "3. Select this repository"
    echo "4. Set Root Directory to: backend"
    echo "5. Add environment variables:"
    echo "   - OPENAI_API_KEY (required)"
    echo "   - OPENAI_PROJECT_ID (optional, if using project keys)"
    echo "6. Copy the public URL (e.g., https://your-app.up.railway.app)"
    echo ""
    read -p "Press Enter when backend is deployed and you have the URL..."
    read -p "Enter your Railway backend URL: " backend_url
    
    echo ""
    echo "Step 2: Deploy Frontend to Vercel"
    echo "----------------------------------"
    echo "1. Go to https://vercel.com and sign up/login"
    echo "2. Click 'Add New Project' → Import from GitHub"
    echo "3. Select this repository"
    echo "4. Set Root Directory to: frontend"
    echo "5. Add environment variable:"
    echo "   - NEXT_PUBLIC_BACKEND_URL = $backend_url"
    echo "6. Deploy!"
    echo ""
    echo "✅ After deployment, your frontend URL will be available in Vercel dashboard"
    ;;
    
  2)
    echo ""
    echo "📦 Deploying to Render + Vercel"
    echo ""
    echo "Step 1: Deploy Backend to Render"
    echo "----------------------------------"
    echo "1. Go to https://render.com and sign up/login"
    echo "2. Click 'New' → 'Web Service'"
    echo "3. Connect GitHub and select this repository"
    echo "4. Configure:"
    echo "   - Build Command: pip install -r requirements.txt"
    echo "   - Start Command: cd backend && uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
    echo "   - Environment: Python 3"
    echo "5. Add environment variables (same as Railway)"
    echo "6. Copy the public URL"
    echo ""
    read -p "Press Enter when backend is deployed..."
    read -p "Enter your Render backend URL: " backend_url
    
    echo ""
    echo "Step 2: Deploy Frontend to Vercel (same as above)"
    echo "Use NEXT_PUBLIC_BACKEND_URL = $backend_url"
    ;;
    
  3)
    echo ""
    echo "🔗 Quick Test with ngrok"
    echo "-------------------------"
    echo "This will expose your local development servers to the internet"
    echo ""
    echo "Prerequisites:"
    echo "- Install ngrok: https://ngrok.com/download"
    echo "- Backend running on port 8000"
    echo "- Frontend running on port 3000"
    echo ""
    read -p "Press Enter to continue..."
    
    echo ""
    echo "Starting ngrok tunnels..."
    echo "Backend tunnel (port 8000):"
    ngrok http 8000 --log=stdout > /tmp/ngrok-backend.log &
    BACKEND_PID=$!
    sleep 2
    
    echo "Frontend tunnel (port 3000):"
    ngrok http 3000 --log=stdout > /tmp/ngrok-frontend.log &
    FRONTEND_PID=$!
    sleep 2
    
    echo ""
    echo "✅ ngrok tunnels started!"
    echo "Check the ngrok web interface at http://localhost:4040"
    echo "Or check logs:"
    echo "  Backend: tail -f /tmp/ngrok-backend.log"
    echo "  Frontend: tail -f /tmp/ngrok-frontend.log"
    echo ""
    echo "Update frontend/.env.local with:"
    echo "NEXT_PUBLIC_BACKEND_URL=<your-ngrok-backend-url>"
    echo ""
    echo "Press Ctrl+C to stop ngrok tunnels"
    wait
    ;;
    
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac
