#!/bin/bash
# Install n10s plugin manually (without recreating container)
# This preserves existing data

echo "=== Installing n10s Plugin (Manual Method) ==="
echo ""

NEO4J_CONTAINER_NAME="neo4j-local"
NEO4J_VERSION="5.19.0"
N10S_VERSION="5.18.0"  # Compatible with Neo4j 5.19

echo "1. Downloading n10s JAR..."
N10S_URL="https://github.com/neo4j-labs/neosemantics/releases/download/${N10S_VERSION}/neosemantics-${N10S_VERSION}.jar"
N10S_JAR="/tmp/neosemantics-${N10S_VERSION}.jar"

if [ ! -f "$N10S_JAR" ]; then
    echo "   Downloading from: $N10S_URL"
    curl -L -o "$N10S_JAR" "$N10S_URL"
    
    if [ ! -f "$N10S_JAR" ] || [ $(stat -f%z "$N10S_JAR" 2>/dev/null || stat -c%s "$N10S_JAR" 2>/dev/null) -lt 1000 ]; then
        echo "❌ Download failed or file too small"
        echo "   Please download manually from:"
        echo "   https://github.com/neo4j-labs/neosemantics/releases"
        exit 1
    fi
else
    echo "   Using existing file: $N10S_JAR"
fi

echo ""
echo "2. Copying JAR to Neo4j container..."
docker cp "$N10S_JAR" ${NEO4J_CONTAINER_NAME}:/var/lib/neo4j/plugins/

if [ $? -ne 0 ]; then
    echo "❌ Failed to copy JAR to container"
    exit 1
fi

echo "3. Setting permissions..."
docker exec ${NEO4J_CONTAINER_NAME} chown neo4j:neo4j /var/lib/neo4j/plugins/neosemantics-${N10S_VERSION}.jar
docker exec ${NEO4J_CONTAINER_NAME} chmod 644 /var/lib/neo4j/plugins/neosemantics-${N10S_VERSION}.jar

echo ""
echo "4. Restarting Neo4j container..."
docker restart ${NEO4J_CONTAINER_NAME}

echo ""
echo "5. Waiting 30 seconds for Neo4j to restart..."
sleep 30

echo ""
echo "6. Verifying installation..."
docker exec ${NEO4J_CONTAINER_NAME} cypher-shell -u neo4j -p test12345 "SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'n10s' RETURN name LIMIT 5;" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ n10s plugin installed successfully!"
    echo ""
    echo "⚠️  Note: If Neo4j doesn't start, check logs:"
    echo "   docker logs ${NEO4J_CONTAINER_NAME}"
else
    echo ""
    echo "⚠️  Verification failed. Check logs:"
    docker logs ${NEO4J_CONTAINER_NAME} | tail -n 30
fi

