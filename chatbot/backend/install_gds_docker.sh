#!/bin/bash
# Install Neo4j GDS in Docker container
# For Neo4j 5.19.0

echo "=== Installing Neo4j GDS for Neo4j 5.19.0 ==="
echo ""

# GDS version compatible with Neo4j 5.19
# Using 2.13.4 (stable release compatible with Neo4j 5.x)
GDS_VERSION="2.13.4"
GDS_JAR="neo4j-graph-data-science-${GDS_VERSION}.jar"
GDS_URL="https://github.com/neo4j/graph-data-science/releases/download/${GDS_VERSION}/${GDS_JAR}"

echo "1. Downloading GDS ${GDS_VERSION}..."
cd /tmp
curl -L -O "${GDS_URL}"

if [ ! -f "${GDS_JAR}" ]; then
    echo "❌ Download failed. Please download manually from:"
    echo "   https://github.com/neo4j/graph-data-science/releases/download/${GDS_VERSION}/${GDS_JAR}"
    exit 1
fi

echo "✅ Downloaded ${GDS_JAR}"

echo ""
echo "2. Copying GDS to Neo4j container..."
docker cp "${GDS_JAR}" neo4j-local:/var/lib/neo4j/plugins/

echo "✅ Copied to container"

echo ""
echo "3. Verifying JAR file size (should be > 50MB)..."
JAR_SIZE=$(stat -f%z "${GDS_JAR}" 2>/dev/null || stat -c%s "${GDS_JAR}" 2>/dev/null)
if [ "$JAR_SIZE" -lt 50000000 ]; then
    echo "❌ JAR file too small (${JAR_SIZE} bytes). Download may have failed."
    echo "   Please check the file manually."
    exit 1
fi
echo "✅ JAR file size: $((JAR_SIZE / 1024 / 1024))MB"

echo ""
echo "4. Restarting Neo4j container..."
docker restart neo4j-local

echo ""
echo "5. Waiting for Neo4j to start (45 seconds)..."
sleep 45

echo ""
echo "6. Checking container status..."
if ! docker ps --filter "name=neo4j-local" --format "{{.Names}}" | grep -q neo4j-local; then
    echo "❌ Container is not running. Checking logs..."
    docker logs neo4j-local --tail 20
    echo ""
    echo "⚠️  Container may have failed to start. Check logs above."
    exit 1
fi
echo "✅ Container is running"

echo ""
echo "7. Verifying GDS installation..."
sleep 5
docker exec neo4j-local cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-neo4j}" \
  "CALL gds.version() YIELD version RETURN version;" 2>&1 | grep -v "password change" || {
    echo "⚠️  GDS verification failed. Container may still be starting."
    echo "   Wait a bit longer and run manually:"
    echo "   docker exec neo4j-local cypher-shell -u neo4j -p your_password 'CALL gds.version() YIELD version RETURN version;'"
}

echo ""
echo "✅ Installation complete!"
echo ""
echo "To verify, run:"
echo "  docker exec neo4j-local cypher-shell -u neo4j -p your_password 'CALL gds.version() YIELD version RETURN version;'"
