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
lsof -ti :3001 | xargs kill -9 2>/dev/null || true
lsof -ti :8081 | xargs kill -9 2>/dev/null || true
lsof -ti :7687 | xargs kill -9 2>/dev/null || true
sleep 2
echo "✅ Ports cleared"
echo ""

# Step 2: Start Docker containers
echo "📋 Step 2: Starting Docker containers..."

# Check if Docker is accessible
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not accessible. Please ensure Docker Desktop is running."
    exit 1
fi

# Check if containers are running
RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}" 2>/dev/null)
NEO4J_RUNNING=false
POSTGRES_RUNNING=false

if echo "$RUNNING_CONTAINERS" | grep -q "neo4j-local"; then
    NEO4J_RUNNING=true
fi
if echo "$RUNNING_CONTAINERS" | grep -q "postgres-local-snp"; then
    POSTGRES_RUNNING=true
fi

if [ "$NEO4J_RUNNING" = true ] && [ "$POSTGRES_RUNNING" = true ]; then
    echo "✅ Containers are already running"
elif [ "$NEO4J_RUNNING" = true ] || [ "$POSTGRES_RUNNING" = true ]; then
    echo "⚠️  Some containers are running, starting the rest..."
    if [ "$NEO4J_RUNNING" = false ]; then
        docker start neo4j-local 2>/dev/null && echo "   ✅ Started neo4j-local" || echo "   ⚠️  neo4j-local not found or already running"
    fi
    if [ "$POSTGRES_RUNNING" = false ]; then
        docker start postgres-local-snp 2>/dev/null && echo "   ✅ Started postgres-local-snp" || echo "   ⚠️  postgres-local-snp not found or already running"
    fi
else
    echo "⚠️  Containers not running. Attempting to start..."
    if docker start postgres-local-snp neo4j-local 2>/dev/null; then
        echo "✅ Containers started"
    else
        echo "⚠️  Could not start containers. They may not exist."
        echo "   Running setup script to create them..."
        if [ -f "$SCRIPT_DIR/setup_docker_containers.sh" ]; then
            "$SCRIPT_DIR/setup_docker_containers.sh"
        else
            echo "❌ Setup script not found. Please run: ./setup_docker_containers.sh"
            exit 1
        fi
    fi
fi

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
echo "📋 Step 4: Starting Frontend (on port 3001)..."
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
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo "✅ Frontend is running at http://localhost:3001"
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
echo "   • Frontend:   http://localhost:3001"
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

