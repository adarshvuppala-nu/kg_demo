#!/bin/bash
# Start Ontop using Docker (from ontop-tutorial)

echo "=== Starting Ontop VKG Endpoint via Docker ==="
echo ""

# Check if PostgreSQL is running
if ! docker ps | grep -q postgres-local-snp; then
    echo "⚠️  PostgreSQL container not running. Starting it..."
    docker start postgres-local-snp || docker run -d --name postgres-local-snp \
        -p 5434:5432 \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=kg_demo \
        postgres:15
    sleep 5
fi

# Navigate to ontop tutorial endpoint directory
ONTOP_TUTORIAL_DIR="/Users/adarshvuppala/kg_demo/ontop/ontop-tutorial/endpoint"

if [ ! -d "$ONTOP_TUTORIAL_DIR" ]; then
    echo "❌ Ontop tutorial directory not found: $ONTOP_TUTORIAL_DIR"
    exit 1
fi

cd "$ONTOP_TUTORIAL_DIR"

echo "Using Ontop tutorial Docker setup..."
echo ""
echo "To use your stock data:"
echo "   1. Copy your files to ontop-tutorial/endpoint/input/:"
echo "      - stock_mapping.obda"
echo "      - stock_ontology_ontop.owl"
echo "      - stock_ontop.properties"
echo ""
echo "   2. Modify docker-compose.yml to use PostgreSQL"
echo "   3. Run: docker-compose up"
echo ""
echo "Or use the existing university example to test Ontop first:"
read -p "Start Ontop with university example? (y/N): " use_example

if [ "$use_example" = "y" ] || [ "$use_example" = "Y" ]; then
    echo ""
    echo "Starting Ontop with university example..."
    docker-compose up -d
    
    echo ""
    echo "✅ Ontop started!"
    echo "   Access: http://localhost:8080"
    echo "   SPARQL: http://localhost:8080/sparql"
    echo ""
    echo "To stop: docker-compose down"
else
    echo ""
    echo "To customize for your stock data:"
    echo "   1. Copy files to $ONTOP_TUTORIAL_DIR/input/"
    echo "   2. Modify docker-compose.yml"
    echo "   3. Run: docker-compose up"
fi

