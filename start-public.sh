#!/bin/bash

set -e

echo "🚀 Starting Public Deployment"
echo "============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
check_backend() {
    curl -s http://localhost:8000/api/health > /dev/null 2>&1 || return 1
    return 0
}

# Check if frontend is running
check_frontend() {
    curl -s http://localhost:3000 > /dev/null 2>&1 || return 1
    return 0
}

# Start backend
echo -e "${BLUE}📦 Starting Backend...${NC}"
cd backend

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv and install dependencies
source .venv/bin/activate
pip install -q -r requirements.txt

# Start backend in background
echo "Starting FastAPI server on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..30}; do
    if check_backend; then
        echo -e "${GREEN}✅ Backend is running!${NC}"
        break
    fi
    sleep 1
done

if ! check_backend; then
    echo -e "${YELLOW}⚠️  Backend may not be fully ready, but continuing...${NC}"
fi

# Start frontend
echo ""
echo -e "${BLUE}📦 Starting Frontend...${NC}"
cd ../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
echo "Starting Next.js server on port 3000..."
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo "Waiting for frontend to start..."
for i in {1..30}; do
    if check_frontend; then
        echo -e "${GREEN}✅ Frontend is running!${NC}"
        break
    fi
    sleep 1
done

# Start ngrok tunnel for frontend (which will proxy to backend)
echo ""
echo -e "${BLUE}🌐 Starting ngrok tunnel...${NC}"

# Start frontend ngrok (frontend proxies API calls to backend)
echo "Exposing frontend (port 3000)..."
ngrok http 3000 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
sleep 5

# Get ngrok URL
FRONTEND_NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') and len(data['tunnels']) > 0 else '')" 2>/dev/null || echo "")

if [ -z "$FRONTEND_NGROK_URL" ]; then
    # Try alternative parsing
    FRONTEND_NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[^"]*\.ngrok[^"]*' | head -1 || echo "")
fi

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=============================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""

if [ -n "$FRONTEND_NGROK_URL" ]; then
    echo -e "${GREEN}🌐 Public URL: $FRONTEND_NGROK_URL${NC}"
    echo ""
    echo -e "${BLUE}✅ Your app is accessible at: $FRONTEND_NGROK_URL${NC}"
else
    echo -e "${YELLOW}⚠️  ngrok URL not found. Check http://localhost:4040${NC}"
    echo "The frontend proxies API calls to the local backend automatically."
fi

echo ""
echo "View ngrok dashboard: http://localhost:4040"
echo ""
echo "Press Ctrl+C to stop all services"

# Create cleanup script
cat > /tmp/stop-deployment.sh << 'EOF'
#!/bin/bash
pkill -f "uvicorn app.main:app" || true
pkill -f "next dev" || true
pkill -f "ngrok http" || true
echo "✅ All services stopped"
EOF
chmod +x /tmp/stop-deployment.sh

echo "To stop all services, run: /tmp/stop-deployment.sh"
echo ""

# Wait for user interrupt
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID $NGROK_PID 2>/dev/null; /tmp/stop-deployment.sh; exit" INT

wait
