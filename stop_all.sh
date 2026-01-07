#!/bin/bash
# Stop all services for GraphRAG demo

echo "═══════════════════════════════════════════════════════════════"
echo "           GraphRAG Demo - Stopping All Services"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Stop processes on ports
echo "📋 Stopping services on ports..."
lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "✅ Backend stopped (port 8000)" || echo "⚠️  No process on port 8000"
lsof -ti :3000 | xargs kill -9 2>/dev/null && echo "✅ Frontend stopped (port 3000)" || echo "⚠️  No process on port 3000"
lsof -ti :8081 | xargs kill -9 2>/dev/null && echo "✅ Ontop stopped (port 8081)" || echo "⚠️  No process on port 8081"
lsof -ti :7687 | xargs kill -9 2>/dev/null && echo "✅ Neo4j client stopped (port 7687)" || echo "⚠️  No process on port 7687"

sleep 2

# Stop Docker containers
echo ""
echo "📋 Stopping Docker containers..."
docker stop postgres-local-snp 2>/dev/null && echo "✅ PostgreSQL stopped" || echo "⚠️  PostgreSQL container not running"
docker stop neo4j-local 2>/dev/null && echo "✅ Neo4j stopped" || echo "⚠️  Neo4j container not running"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    ✅ ALL SERVICES STOPPED"
echo "═══════════════════════════════════════════════════════════════"

