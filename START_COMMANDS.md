# GraphRAG Demo - Startup Commands

## Quick Start (All Services)

### Option 1: Use the startup script (Recommended)
```bash
cd /Users/adarshvuppala/kg_demo
chmod +x start_all.sh stop_all.sh
./start_all.sh
```

### Option 2: Manual startup (Step by step)

#### 1. Start Docker Containers
```bash
docker start postgres-local-snp neo4j-local
```

Wait 10-15 seconds for containers to be ready.

#### 2. Start Backend (FastAPI)
```bash
cd /Users/adarshvuppala/kg_demo/chatbot/backend
source /Users/adarshvuppala/kg_demo/venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Or run in background:
```bash
cd /Users/adarshvuppala/kg_demo/chatbot/backend
source /Users/adarshvuppala/kg_demo/venv/bin/activate
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
```

#### 3. Start Frontend
```bash
cd /Users/adarshvuppala/kg_demo/chatbot/frontend
npm start
```

Or run in background:
```bash
cd /Users/adarshvuppala/kg_demo/chatbot/frontend
nohup npm start > /tmp/frontend.log 2>&1 &
```

#### 4. Start Ontop (Optional)
```bash
cd /Users/adarshvuppala/kg_demo/chatbot/backend
./start_ontop.sh
```

Or run in background:
```bash
cd /Users/adarshvuppala/kg_demo/chatbot/backend
nohup ./start_ontop.sh > /tmp/ontop.log 2>&1 &
```

---

## Stop All Services

### Option 1: Use the stop script
```bash
cd /Users/adarshvuppala/kg_demo
./stop_all.sh
```

### Option 2: Manual stop

#### Stop processes on ports
```bash
lsof -ti :8000 | xargs kill -9  # Backend
lsof -ti :3000 | xargs kill -9  # Frontend
lsof -ti :8081 | xargs kill -9  # Ontop
```

#### Stop Docker containers
```bash
docker stop postgres-local-snp neo4j-local
```

---

## Service URLs

- **PostgreSQL**: `localhost:5434`
- **Neo4j Browser**: `http://localhost:7474`
- **Backend API**: `http://localhost:8000`
- **Frontend**: `http://localhost:3000`
- **Ontop SPARQL**: `http://localhost:8081/sparql`

---

## Verify Services

### Check Docker containers
```bash
docker ps | grep -E "(postgres|neo4j)"
```

### Check ports
```bash
lsof -i :8000  # Backend
lsof -i :3000   # Frontend
lsof -i :8081   # Ontop
lsof -i :5434   # PostgreSQL
lsof -i :7474   # Neo4j HTTP
lsof -i :7687   # Neo4j Bolt
```

### Test endpoints
```bash
curl http://localhost:8000/              # Backend health
curl http://localhost:3000               # Frontend
curl http://localhost:8081/sparql       # Ontop
```

---

## Troubleshooting

### Backend not starting
```bash
# Check logs
tail -f /tmp/backend.log

# Check if port is in use
lsof -i :8000

# Restart
kill -9 $(lsof -ti :8000)
cd /Users/adarshvuppala/kg_demo/chatbot/backend
source /Users/adarshvuppala/kg_demo/venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend not starting
```bash
# Check logs
tail -f /tmp/frontend.log

# Reinstall dependencies if needed
cd /Users/adarshvuppala/kg_demo/chatbot/frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### Docker containers not starting
```bash
# Check container status
docker ps -a | grep -E "(postgres|neo4j)"

# Start containers
docker start postgres-local-snp neo4j-local

# Check logs
docker logs postgres-local-snp
docker logs neo4j-local
```

### Neo4j not responding
```bash
# Wait longer (Neo4j takes 10-15 seconds to start)
sleep 15
curl http://localhost:7474

# Check Neo4j logs
docker logs neo4j-local
```

---

## Complete Restart (Clean)

```bash
# Stop everything
./stop_all.sh

# Wait a moment
sleep 3

# Start everything
./start_all.sh
```

