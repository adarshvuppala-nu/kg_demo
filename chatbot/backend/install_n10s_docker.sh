#!/bin/bash
# Install Neo4j n10s (neosemantics) plugin in Docker container
# Uses NEO4JLABS_PLUGINS environment variable (recommended method)

echo "=== Installing Neo4j n10s Plugin ==="
echo ""

NEO4J_CONTAINER_NAME="neo4j-local"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-test12345}"

echo "This script will recreate your Neo4j container with n10s plugin."
echo "⚠️  WARNING: This will stop and remove the existing container!"
echo ""
read -p "Continue? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "1. Stopping and removing existing container..."
docker stop ${NEO4J_CONTAINER_NAME} 2>/dev/null
docker rm ${NEO4J_CONTAINER_NAME} 2>/dev/null

echo "2. Creating new Neo4j container with n10s plugin..."
docker run -d --name ${NEO4J_CONTAINER_NAME} \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/${NEO4J_PASSWORD} \
  -e NEO4JLABS_PLUGINS='["n10s"]' \
  neo4j:5.19

echo "3. Waiting 45 seconds for Neo4j to start and n10s to install..."
sleep 45

echo "4. Verifying n10s installation..."
VERIFY_CMD="CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'n10s' RETURN name LIMIT 5;"
docker exec ${NEO4J_CONTAINER_NAME} cypher-shell -u neo4j -p ${NEO4J_PASSWORD} "${VERIFY_CMD}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ n10s plugin installed successfully!"
    echo ""
    echo "⚠️  IMPORTANT: Your data was in the old container!"
    echo "   You need to reload data:"
    echo "   1. python load_data_to_neo4j.py"
    echo "   2. python load_schema_extension.py"
    echo "   3. python gds_setup.py"
    echo ""
    echo "Then import ontology:"
    echo "   python import_n10s_ontology.py"
else
    echo ""
    echo "❌ n10s verification failed. Check logs:"
    docker logs ${NEO4J_CONTAINER_NAME} | tail -n 30
fi

