# Manual Commands - Step by Step

## Quick Reference

### 1. Check Docker is Running
```bash
docker ps
```
If this works, Docker is running. If you get an error, start Docker Desktop.

---

### 2. Start Docker Containers
```bash
docker start neo4j-local postgres-local-snp
```

Wait 15 seconds for Neo4j to fully start.

**Verify containers are running:**
```bash
docker ps | grep -E "(neo4j|postgres)"
```

You should see both containers listed.

---

### 3. Start Backend (Terminal 1)

Open a new terminal and run:
```bash
cd /Users/adarshvuppala/kg_demo/chatbot/backend
source /Users/adarshvuppala/kg_demo/venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Keep this terminal open!** You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test backend:**
```bash
curl http://localhost:8000/
```
Should return: `{"status":"ok"}`

---

### 4. Start Frontend (Terminal 2 - NEW TERMINAL)

Open a **second** terminal and run:
```bash
cd /Users/adarshvuppala/kg_demo/chatbot/frontend
npm start
```

**Keep this terminal open!** Then open your browser to `http://localhost:3001`

---

### 5. Access Services

- **Frontend Chatbot**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `test12345`

---

## Troubleshooting

### Backend won't start?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process on port 8000
lsof -ti :8000 | xargs kill -9

# Try starting again
cd /Users/adarshvuppala/kg_demo/chatbot/backend
source /Users/adarshvuppala/kg_demo/venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend won't start?
```bash
# Check if port 3001 is in use
lsof -i :3001

# Kill process on port 3001
lsof -ti :3001 | xargs kill -9

# Install dependencies if needed
cd /Users/adarshvuppala/kg_demo/chatbot/frontend
npm install

# Try starting again
npm start
```

### Neo4j not accessible?
```bash
# Check if container is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs neo4j-local | tail -20

# Restart Neo4j
docker restart neo4j-local

# Wait 15 seconds, then try again
```

### PostgreSQL not accessible?
```bash
# Check if container is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs postgres-local-snp | tail -20

# Restart PostgreSQL
docker restart postgres-local-snp
```

---

## Stop Everything

### Stop Backend
Press `Ctrl+C` in the backend terminal

### Stop Frontend
Press `Ctrl+C` in the frontend terminal

### Stop Docker Containers
```bash
docker stop neo4j-local postgres-local-snp
```

---

## Complete Restart

If everything is broken, start fresh:

```bash
# 1. Stop everything
docker stop neo4j-local postgres-local-snp
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :3001 | xargs kill -9 2>/dev/null

# 2. Start containers
docker start neo4j-local postgres-local-snp

# 3. Wait 15 seconds

# 4. Start backend (Terminal 1)
cd /Users/adarshvuppala/kg_demo/chatbot/backend
source /Users/adarshvuppala/kg_demo/venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 5. Start frontend (Terminal 2)
cd /Users/adarshvuppala/kg_demo/chatbot/frontend
npm start
```

---

## Verify Everything Works

```bash
# 1. Check Docker containers
docker ps | grep -E "(neo4j|postgres)"

# 2. Check backend
curl http://localhost:8000/

# 3. Check frontend
curl http://localhost:3001 | head -5

# 4. Check Neo4j
curl http://localhost:7474 | head -5
```

All should return success!

