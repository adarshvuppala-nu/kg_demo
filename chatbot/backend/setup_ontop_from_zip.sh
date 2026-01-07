#!/bin/bash
# Helper script to extract and setup Ontop from downloaded ZIP

echo "=== Ontop Setup Helper ==="
echo ""

# Check if ZIP file exists in common locations
ZIP_FILE=""
possible_locations=(
    "$HOME/Downloads/ontop-cli-5.4.0.zip"
    "$HOME/Desktop/ontop-cli-5.4.0.zip"
    "./ontop-cli-5.4.0.zip"
    "/tmp/ontop-cli-5.4.0.zip"
)

for location in "${possible_locations[@]}"; do
    if [ -f "$location" ]; then
        ZIP_FILE="$location"
        echo "✅ Found ZIP file: $ZIP_FILE"
        break
    fi
done

if [ -z "$ZIP_FILE" ]; then
    echo "❌ ontop-cli-5.4.0.zip not found in common locations"
    echo ""
    echo "Please provide the path to the downloaded ZIP file:"
    read -p "ZIP file path: " ZIP_FILE
    
    if [ ! -f "$ZIP_FILE" ]; then
        echo "❌ File not found: $ZIP_FILE"
        exit 1
    fi
fi

echo ""
echo "Extracting ZIP file..."
TEMP_DIR=$(mktemp -d)
unzip -q "$ZIP_FILE" -d "$TEMP_DIR"

# The ZIP extracts to a directory (usually ontop-cli-5.4.0) inside TEMP_DIR
# Find the extracted directory
EXTRACTED_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d ! -path "$TEMP_DIR" | head -1)

# If no subdirectory, files are directly in TEMP_DIR
if [ -z "$EXTRACTED_DIR" ] || [ ! -d "$EXTRACTED_DIR" ]; then
    EXTRACTED_DIR="$TEMP_DIR"
fi

echo "✅ Extracted to: $EXTRACTED_DIR"

# Check for ontop executable wrapper (preferred method)
ONTOP_EXECUTABLE=$(find "$EXTRACTED_DIR" -maxdepth 2 -name "ontop" -type f -perm +111 | head -1)

if [ -n "$ONTOP_EXECUTABLE" ]; then
    echo "✅ Found ontop executable: $ONTOP_EXECUTABLE"
    # Get the directory containing the executable
    ONTOP_BASE_DIR=$(dirname "$ONTOP_EXECUTABLE")
    echo "   Copying entire directory to /tmp/ontop-cli-5.4.0..."
    rm -rf /tmp/ontop-cli-5.4.0
    cp -r "$ONTOP_BASE_DIR" /tmp/ontop-cli-5.4.0
    echo "✅ Ontop directory copied to /tmp/ontop-cli-5.4.0"
    ONTOP_SETUP="directory"
else
    # Fallback: find and copy JAR (needs classpath setup)
    JAR_FILE=$(find "$EXTRACTED_DIR" -name "ontop-cli*.jar" -type f | head -1)
    
    if [ -z "$JAR_FILE" ]; then
        JAR_FILE=$(find "$EXTRACTED_DIR" -path "*/lib/ontop-cli*.jar" -type f | head -1)
    fi
    
    if [ -n "$JAR_FILE" ]; then
        echo "✅ Found JAR: $JAR_FILE"
        echo "   Note: JAR needs classpath - copying entire directory is recommended"
        # Copy entire directory for classpath
        ONTOP_BASE_DIR=$(dirname "$(dirname "$JAR_FILE")")
        if [ "$ONTOP_BASE_DIR" = "$TEMP_DIR" ] || [ "$ONTOP_BASE_DIR" = "$EXTRACTED_DIR" ]; then
            ONTOP_BASE_DIR="$EXTRACTED_DIR"
        fi
        rm -rf /tmp/ontop-cli-5.4.0
        cp -r "$ONTOP_BASE_DIR" /tmp/ontop-cli-5.4.0
        ONTOP_SETUP="directory"
    else
        echo "❌ Could not find ontop executable or JAR"
        echo "   Contents:"
        ls -la "$EXTRACTED_DIR" | head -10
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# Verify
echo ""
echo "Verifying Ontop installation..."

if [ "$ONTOP_SETUP" = "directory" ]; then
    # Test using the executable wrapper
    if [ -f /tmp/ontop-cli-5.4.0/ontop ]; then
        VERSION_OUTPUT=$(/tmp/ontop-cli-5.4.0/ontop --version 2>&1)
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ] || echo "$VERSION_OUTPUT" | grep -q "Ontop\|5.4"; then
            echo "✅ Ontop is valid!"
            echo "   Using executable: /tmp/ontop-cli-5.4.0/ontop"
            echo ""
            echo "✅ Setup complete! You can now run:"
            echo "   ./start_ontop.sh"
        else
            echo "⚠️  Version check had issues, but files are in place"
            echo "   Try running: ./start_ontop.sh"
        fi
    else
        echo "❌ ontop executable not found"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
else
    # Try to get version from JAR
    VERSION_OUTPUT=$(java -jar /tmp/ontop-cli.jar --version 2>&1)
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ] || echo "$VERSION_OUTPUT" | grep -q "Ontop\|version\|5.4"; then
        VERSION=$(echo "$VERSION_OUTPUT" | head -1)
        echo "✅ Ontop JAR is valid!"
        echo "   Version info: $VERSION"
    else
        if [ -f /tmp/ontop-cli.jar ] && [ -s /tmp/ontop-cli.jar ]; then
            JAR_SIZE=$(ls -lh /tmp/ontop-cli.jar | awk '{print $5}')
            echo "⚠️  Version check failed, but JAR file exists ($JAR_SIZE)"
        else
            echo "❌ JAR verification failed - file may be corrupted"
            rm -rf "$TEMP_DIR"
            exit 1
        fi
    fi
    echo ""
    echo "✅ Setup complete! You can now run:"
    echo "   ./start_ontop.sh"
fi

# Cleanup
rm -rf "$TEMP_DIR"

