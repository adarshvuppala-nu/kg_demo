#!/bin/bash
# Complete startup script for GraphRAG demo
# Run this script to start all services

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "           GraphRAG Demo - Starting All Services"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Stop any existing services
echo "📋 Step 1: Stopping existing services..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :3000 | xargs kill -9 2>/dev/null || true
lsof -ti :8081 | xargs kill -9 2>/dev/null || true
lsof -ti :7687 | xargs kill -9 2>/dev/null || true
sleep 2
echo "✅ Ports cleared"
echo ""

# Step 2: Start Docker containers
echo "📋 Step 2: Starting Docker containers..."
docker start postgres-local-snp neo4j-local 2>/dev/null || {
    echo "⚠️  Containers not found. Please ensure they exist:"
    echo "   docker ps -a | grep -E '(postgres|neo4j)'"
    exit 1
}

echo "⏳ Waiting for containers to be ready..."
sleep 5

# Check PostgreSQL
echo -n "   Checking PostgreSQL... "
for i in {1..10}; do
    if docker exec postgres-local-snp pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅"
        break
    fi
    sleep 1
done

# Check Neo4j
echo -n "   Checking Neo4j... "
for i in {1..30}; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "✅"
        break
    fi
    sleep 1
done

echo "✅ Docker containers ready"
echo ""

# Step 3: Start Backend (FastAPI)
echo "📋 Step 3: Starting Backend (FastAPI on port 8000)..."
cd "$SCRIPT_DIR/chatbot/backend"
source "$SCRIPT_DIR/venv/bin/activate" 2>/dev/null || {
    echo "⚠️  Virtual environment not found. Please create it first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
}

# Start backend in background
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "⚠️  Backend may still be starting. Check logs: tail -f /tmp/backend.log"
fi
echo ""

# Step 4: Start Frontend (if needed)
echo "📋 Step 4: Starting Frontend (on port 3000)..."
cd "$SCRIPT_DIR/chatbot/frontend"

# Check if we need to install dependencies
if [ ! -d "node_modules" ]; then
    echo "   Installing frontend dependencies..."
    npm install > /dev/null 2>&1 || {
        echo "⚠️  npm install failed. Please install manually:"
        echo "   cd chatbot/frontend && npm install"
    }
fi

# Start frontend in background
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
sleep 5

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "⚠️  Frontend may still be starting. Check logs: tail -f /tmp/frontend.log"
fi
echo ""

# Step 5: Start Ontop (optional)
echo "📋 Step 5: Starting Ontop VKG (optional, on port 8081)..."
if [ -f "$SCRIPT_DIR/chatbot/backend/start_ontop.sh" ]; then
    cd "$SCRIPT_DIR/chatbot/backend"
    nohup ./start_ontop.sh > /tmp/ontop.log 2>&1 &
    ONTOP_PID=$!
    echo "   Ontop PID: $ONTOP_PID"
    sleep 5
    
    if curl -s http://localhost:8081/sparql > /dev/null 2>&1; then
        echo "✅ Ontop is running at http://localhost:8081/sparql"
    else
        echo "⚠️  Ontop may still be starting. Check logs: tail -f /tmp/ontop.log"
    fi
else
    echo "⚠️  Ontop script not found. Skipping..."
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "                    ✅ ALL SERVICES STARTED"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📍 Services:"
echo "   • PostgreSQL:  localhost:5434"
echo "   • Neo4j:      http://localhost:7474 (Browser)"
echo "   • Backend:    http://localhost:8000"
echo "   • Frontend:   http://localhost:3000"
echo "   • Ontop:      http://localhost:8081/sparql (if started)"
echo ""
echo "📋 Process IDs (for stopping later):"
echo "   Backend: $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
[ ! -z "$ONTOP_PID" ] && echo "   Ontop: $ONTOP_PID"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo "   Ontop:    tail -f /tmp/ontop.log"
echo ""
echo "🛑 To stop all services, run: ./stop_all.sh"
echo "═══════════════════════════════════════════════════════════════"

