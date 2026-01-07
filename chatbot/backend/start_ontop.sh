#!/bin/bash
# Start Ontop VKG Endpoint with stock data mapping

echo "=== Starting Ontop VKG Endpoint ==="
echo ""

# Configuration
ONTOP_DIR="/Users/adarshvuppala/kg_demo/ontop"
MAPPING_FILE="/Users/adarshvuppala/kg_demo/chatbot/backend/stock_mapping.obda"
ONTOLOGY_FILE="/Users/adarshvuppala/kg_demo/chatbot/backend/stock_ontology_ontop.owl"
PROPERTIES_FILE="/Users/adarshvuppala/kg_demo/chatbot/backend/stock_ontop.properties"
PORT=8081

# Check if files exist
if [ ! -f "$MAPPING_FILE" ]; then
    echo "❌ Mapping file not found: $MAPPING_FILE"
    exit 1
fi

if [ ! -f "$ONTOLOGY_FILE" ]; then
    echo "❌ Ontology file not found: $ONTOLOGY_FILE"
    exit 1
fi

if [ ! -f "$PROPERTIES_FILE" ]; then
    echo "❌ Properties file not found: $PROPERTIES_FILE"
    exit 1
fi

# Check for ontop executable wrapper (preferred method)
ONTOP_EXECUTABLE=""
ONTOP_CLI_DIR="/tmp/ontop-cli-5.4.0"

if [ -f "$ONTOP_CLI_DIR/ontop" ] && [ -x "$ONTOP_CLI_DIR/ontop" ]; then
    ONTOP_EXECUTABLE="$ONTOP_CLI_DIR/ontop"
    echo "✅ Found Ontop executable: $ONTOP_EXECUTABLE"
fi

# Find Ontop JAR (fallback)
ONTOP_JAR=""
if [ -z "$ONTOP_EXECUTABLE" ]; then
    possible_locations=(
        "/tmp/ontop-cli.jar"
        "$ONTOP_DIR/ontop-tutorial/endpoint/ontop.jar"
        "$ONTOP_DIR/ontop.jar"
        "$HOME/.ontop/ontop.jar"
        "/usr/local/bin/ontop.jar"
    )

    for location in "${possible_locations[@]}"; do
        if [ -f "$location" ]; then
            ONTOP_JAR="$location"
            break
        fi
    done
fi

# If not found, try to download
if [ -z "$ONTOP_EXECUTABLE" ] && [ -z "$ONTOP_JAR" ]; then
    echo "⚠️  Ontop JAR not found."
    echo ""
    echo "Please download Ontop manually:"
    echo "   1. Go to: https://github.com/ontop/ontop/releases"
    echo "   2. Download: ontop-cli-*.jar (latest version)"
    echo "   3. Save to: /tmp/ontop-cli.jar"
    echo "   4. Or place in: $ONTOP_DIR/"
    echo ""
    echo "Alternatively, use the ontop-tutorial that's already installed:"
    echo "   Check: $ONTOP_DIR/ontop-tutorial/endpoint/"
    echo ""
    read -p "Press Enter after downloading, or Ctrl+C to cancel..."
    
    # Check if user downloaded it
    if [ -f "/tmp/ontop-cli.jar" ]; then
        ONTOP_JAR="/tmp/ontop-cli.jar"
    elif [ -f "$ONTOP_DIR/ontop-cli.jar" ]; then
        ONTOP_JAR="$ONTOP_DIR/ontop-cli.jar"
    else
        echo "❌ Ontop JAR still not found. Exiting."
        exit 1
    fi
fi

# Change to backend directory for relative paths in properties file
cd /Users/adarshvuppala/kg_demo/chatbot/backend

if [ -n "$ONTOP_EXECUTABLE" ]; then
    echo "✅ Using Ontop executable: $ONTOP_EXECUTABLE"
    echo ""
    echo "Starting Ontop endpoint on port $PORT..."
    echo "   Mapping: $MAPPING_FILE"
    echo "   Ontology: $ONTOLOGY_FILE"
    echo "   Properties: $PROPERTIES_FILE"
    echo ""
    echo "Access SPARQL endpoint at: http://localhost:$PORT/sparql"
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Use executable wrapper (handles classpath automatically)
    "$ONTOP_EXECUTABLE" endpoint \
        --mapping="stock_mapping.obda" \
        --ontology="stock_ontology_ontop.owl" \
        --properties="stock_ontop.properties" \
        --port=$PORT \
        --cors-allowed-origins=*
else
    echo "✅ Using Ontop JAR: $ONTOP_JAR"
    echo ""
    echo "Starting Ontop endpoint on port $PORT..."
    echo "   Mapping: $MAPPING_FILE"
    echo "   Ontology: $ONTOLOGY_FILE"
    echo "   Properties: $PROPERTIES_FILE"
    echo ""
    echo "Access SPARQL endpoint at: http://localhost:$PORT/sparql"
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Start Ontop endpoint using JAR
    java -jar "$ONTOP_JAR" endpoint \
        --mapping="stock_mapping.obda" \
        --ontology="stock_ontology_ontop.owl" \
        --properties="stock_ontop.properties" \
        --port=$PORT \
        --cors-allowed-origins=*
fi

