#!/bin/bash
# Setup Docker containers for GraphRAG demo
# Creates containers if they don't exist

echo "═══════════════════════════════════════════════════════════════"
echo "           Setting Up Docker Containers"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if Docker is running (try multiple methods)
DOCKER_ACCESSIBLE=false
if docker ps > /dev/null 2>&1; then
    DOCKER_ACCESSIBLE=true
elif docker info > /dev/null 2>&1; then
    DOCKER_ACCESSIBLE=true
fi

if [ "$DOCKER_ACCESSIBLE" = false ]; then
    echo "❌ Docker is not running or not accessible!"
    echo ""
    echo "Please:"
    echo "1. Open Docker Desktop"
    echo "2. Wait for it to fully start (whale icon in menu bar)"
    echo "3. Run this script again"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# PostgreSQL Container
echo "📋 Setting up PostgreSQL container..."
if docker ps -a | grep -q "postgres-local-snp"; then
    echo "   ✅ Container exists: postgres-local-snp"
    if ! docker ps | grep -q "postgres-local-snp"; then
        echo "   Starting container..."
        docker start postgres-local-snp
        sleep 3
    fi
else
    echo "   Creating new PostgreSQL container..."
    docker run -d --name postgres-local-snp \
        -p 5434:5432 \
        -e POSTGRES_PASSWORD=postgres123 \
        -e POSTGRES_DB=kg_demo \
        -v postgres-data:/var/lib/postgresql/data \
        postgres:15
    
    echo "   ⏳ Waiting for PostgreSQL to start..."
    sleep 5
    
    # Create table
    echo "   Creating stock_prices table..."
    docker exec -i postgres-local-snp psql -U postgres -d kg_demo << EOF
CREATE TABLE IF NOT EXISTS stock_prices (
    date DATE,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    adj_close DOUBLE PRECISION,
    volume BIGINT,
    symbol TEXT
);
EOF
    echo "   ✅ PostgreSQL container ready"
fi

echo ""

# Neo4j Container
echo "📋 Setting up Neo4j container..."
if docker ps -a | grep -q "neo4j-local"; then
    echo "   ✅ Container exists: neo4j-local"
    if ! docker ps | grep -q "neo4j-local"; then
        echo "   Starting container..."
        docker start neo4j-local
        sleep 10
    fi
else
    echo "   Creating new Neo4j container..."
    docker run -d --name neo4j-local \
        -p 7474:7474 \
        -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/test12345 \
        -e NEO4J_PLUGINS='["graph-data-science"]' \
        -v neo4j-data:/data \
        -v neo4j-logs:/logs \
        neo4j:5.19
    
    echo "   ⏳ Waiting for Neo4j to start (this takes 15-20 seconds)..."
    sleep 20
    
    # Wait for Neo4j to be ready
    for i in {1..30}; do
        if curl -s http://localhost:7474 > /dev/null 2>&1; then
            echo "   ✅ Neo4j is ready!"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    ✅ DOCKER CONTAINERS READY"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(postgres|neo4j|NAMES)"
echo ""
echo "🔗 Access URLs:"
echo "   • PostgreSQL: localhost:5434"
echo "   • Neo4j Browser: http://localhost:7474"
echo "   • Neo4j Bolt: bolt://localhost:7687"
echo ""
echo "📝 Connection Details:"
echo "   Neo4j Username: neo4j"
echo "   Neo4j Password: test12345"
echo ""
echo "⚠️  IMPORTANT: If this is a new setup, you need to load data:"
echo "   1. cd chatbot/backend"
echo "   2. source ../../venv/bin/activate"
echo "   3. python3 load_data_to_neo4j.py"
echo "   4. python3 load_schema_extension.py"
echo "   5. python3 gds_setup.py"
echo ""
echo "═══════════════════════════════════════════════════════════════"

