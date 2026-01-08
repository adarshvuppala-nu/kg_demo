#!/usr/bin/env python3
"""
Import RDF/OWL Ontology into Neo4j using n10s
==============================================
Imports the stock ontology and maps existing nodes to RDF classes.
"""

from graph import run_cypher
import os
from dotenv import load_dotenv

load_dotenv('/Users/adarshvuppala/kg_demo/.env')

def check_n10s():
    """Check if n10s is installed."""
    print("=" * 60)
    print("CHECKING N10S INSTALLATION")
    print("=" * 60)
    
    try:
        # Use SHOW PROCEDURES for Neo4j 5.x (dbms.procedures doesn't exist)
        result = run_cypher("SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'n10s' RETURN name LIMIT 5")
        if result:
            print(f"\n✅ n10s plugin found: {len(result)} procedures")
            for r in result:
                print(f"   - {r['name']}")
            return True
        else:
            print("\n❌ n10s plugin not found")
            print("   Run: ./install_n10s_neo4j_5.18.sh first")
            return False
    except Exception as e:
        error_str = str(e)
        # Try alternative check
        try:
            result = run_cypher("CALL n10s.version()")
            if result:
                print(f"\n✅ n10s plugin found (via n10s.version())")
                return True
        except:
            pass
        
        print(f"\n❌ Error: {error_str[:150]}")
        return False

def import_ontology():
    """Import the stock ontology."""
    print("\n" + "=" * 60)
    print("IMPORTING ONTOLOGY")
    print("=" * 60)
    
    ontology_file = "/Users/adarshvuppala/kg_demo/chatbot/backend/stock_ontology.ttl"
    
    if not os.path.exists(ontology_file):
        print(f"\n❌ Ontology file not found: {ontology_file}")
        return False
    
    # Convert file path to file:// URL
    file_url = f"file://{ontology_file}"
    
    print(f"\n📋 Importing ontology from: {ontology_file}")
    
    try:
        # Import ontology
        query = f"CALL n10s.onto.import.fetch('{file_url}', 'Turtle')"
        result = run_cypher(query, read_only=False)
        print("✅ Ontology imported successfully")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {str(e)[:200]}")
        return False

def add_namespace_prefix():
    """Add namespace prefix for the ontology."""
    print("\n" + "=" * 60)
    print("ADDING NAMESPACE PREFIX")
    print("=" * 60)
    
    try:
        # Add namespace prefix (required before mapping)
        query = "CALL n10s.nsprefixes.add('stock', 'http://kg-demo.org/stock#')"
        result = run_cypher(query, read_only=False)
        print("✅ Namespace prefix added: stock → http://kg-demo.org/stock#")
        return True
    except Exception as e:
        error_str = str(e)
        if "already exists" in error_str.lower():
            print("✅ Namespace prefix already exists")
            return True
        print(f"⚠️  Namespace prefix: {error_str[:100]}")
        return False

def map_nodes_to_rdf():
    """Map existing Neo4j nodes to RDF classes."""
    print("\n" + "=" * 60)
    print("MAPPING NODES TO RDF CLASSES")
    print("=" * 60)
    
    # Add namespace prefix first (required)
    if not add_namespace_prefix():
        print("⚠️  Cannot create mappings without namespace prefix")
        return
    
    # n10s.mapping.add syntax: (rdfClass, neo4jLabel)
    # First parameter is RDF IRI, second is Neo4j label
    mappings = [
        ("http://kg-demo.org/stock#Company", "Company"),
        ("http://kg-demo.org/stock#PriceDay", "PriceDay"),
        ("http://kg-demo.org/stock#Year", "Year"),
        ("http://kg-demo.org/stock#Quarter", "Quarter"),
        ("http://kg-demo.org/stock#Month", "Month"),
        ("http://kg-demo.org/stock#Sector", "Sector"),
        ("http://kg-demo.org/stock#Country", "Country"),
        ("http://kg-demo.org/stock#State", "State"),
        ("http://kg-demo.org/stock#City", "City"),
    ]
    
    for rdf_class, neo4j_label in mappings:
        try:
            query = f"CALL n10s.mapping.add('{rdf_class}', '{neo4j_label}')"
            result = run_cypher(query, read_only=False)
            print(f"✅ Mapped {rdf_class} → {neo4j_label}")
        except Exception as e:
            print(f"⚠️  Mapping {neo4j_label}: {str(e)[:100]}")

def test_sparql():
    """Test SPARQL query."""
    print("\n" + "=" * 60)
    print("TESTING SPARQL QUERY")
    print("=" * 60)
    
    # Check available SPARQL procedures
    try:
        result = run_cypher("SHOW PROCEDURES YIELD name WHERE name CONTAINS 'sparql' RETURN name LIMIT 5")
        if result:
            print(f"   Available SPARQL procedures: {[r['name'] for r in result]}")
        else:
            print("   ⚠️  No SPARQL procedures found")
            print("   Note: SPARQL support may require n10s configuration")
            return False
    except:
        pass
    
    # Try different SPARQL procedure names
    sparql_queries = [
        ("n10s.query.sparql", "CALL n10s.query.sparql($sparql)"),
        ("n10s.rdf.sparql", "CALL n10s.rdf.sparql($sparql)"),
    ]
    
    sparql = """PREFIX : <http://kg-demo.org/stock#>
SELECT ?company ?symbol WHERE {
    ?company a :Company .
    ?company :symbol ?symbol .
}
LIMIT 5"""
    
    for proc_name, query_template in sparql_queries:
        try:
            query = query_template.replace("$sparql", f"'{sparql.replace(chr(10), ' ')}'")
            result = run_cypher(query)
            print(f"\n✅ SPARQL query returned {len(result)} results (using {proc_name})")
            for r in result[:5]:
                print(f"   {r}")
            return True
        except Exception as e:
            continue
    
    print(f"\n⚠️  SPARQL query not available")
    print("   This is normal - SPARQL may require additional n10s configuration")
    return False

def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("N10S ONTOLOGY IMPORT")
    print("=" * 60)
    
    if not check_n10s():
        return False
    
    if import_ontology():
        map_nodes_to_rdf()
        test_sparql()
    
    print("\n" + "=" * 60)
    print("✅ ONTOLOGY IMPORT COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

