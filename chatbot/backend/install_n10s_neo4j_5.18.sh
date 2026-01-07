#!/bin/bash
# Install Neo4j 5.18 with n10s plugin (compatible version)

echo "=== Installing Neo4j 5.18 with n10s Plugin ==="
echo ""

NEO4J_CONTAINER_NAME="neo4j-local"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-test12345}"

echo "⚠️  This will recreate your Neo4j container with Neo4j 5.18"
echo "   (n10s is compatible with 5.18, not 5.19)"
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

echo "2. Creating Neo4j 5.18 container with n10s and GDS plugins..."
docker run -d --name ${NEO4J_CONTAINER_NAME} \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/${NEO4J_PASSWORD} \
  -e NEO4J_PLUGINS='["graph-data-science", "n10s"]' \
  neo4j:5.18

echo "3. Waiting 45 seconds for Neo4j to start and plugins to install..."
sleep 45

echo "4. Verifying plugins..."
echo ""
echo "Checking GDS:"
docker exec ${NEO4J_CONTAINER_NAME} cypher-shell -u neo4j -p ${NEO4J_PASSWORD} "CALL gds.version()" 2>/dev/null | head -3

echo ""
echo "Checking n10s:"
docker exec ${NEO4J_CONTAINER_NAME} cypher-shell -u neo4j -p ${NEO4J_PASSWORD} "CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'n10s' RETURN name LIMIT 3" 2>/dev/null | head -5

echo ""
echo "✅ Neo4j 5.18 with plugins installed!"
echo ""
echo "⚠️  IMPORTANT: You need to reload data:"
echo "   1. python load_data_to_neo4j.py"
echo "   2. python load_schema_extension.py"
echo "   3. python gds_setup.py"
echo "   4. python import_n10s_ontology.py"

