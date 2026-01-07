#!/usr/bin/env python3
"""
Explore n10s Plugin for RDF/OWL Ontologies
===========================================
Creates ontology from stock data schema and explores VKG (Virtual Knowledge Graph) concepts.

Based on stock data schema:
- Company {symbol}
- PriceDay {date, open, high, low, close, adj_close, volume}
- Relationships: HAS_PRICE, CORRELATED_WITH, PERFORMED_IN
"""

from graph import run_cypher
import os
from dotenv import load_dotenv

load_dotenv('/Users/adarshvuppala/kg_demo/.env')

def check_n10s():
    """Check if n10s plugin is installed."""
    print("=" * 60)
    print("CHECKING N10S PLUGIN")
    print("=" * 60)
    
    try:
        result = run_cypher("CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'n10s' RETURN name LIMIT 10")
        if result:
            print(f"\n✅ n10s plugin installed: {len(result)} procedures found")
            for r in result:
                print(f"   - {r['name']}")
            return True
        else:
            print("\n⚠️  n10s plugin not found")
            print("\nInstallation:")
            print("   1. Download from: https://github.com/neo4j-labs/neosemantics/releases")
            print("   2. Copy JAR to Neo4j plugins directory")
            print("   3. Add to neo4j.conf:")
            print("      dbms.unmanaged_extension_classes=n10s.endpoint=/rdf")
            print("   4. Restart Neo4j")
            return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)[:100]}")
        return False

def create_stock_ontology_rdf():
    """Create RDF/OWL ontology for stock data schema."""
    print("\n" + "=" * 60)
    print("CREATING STOCK DATA ONTOLOGY (RDF/OWL)")
    print("=" * 60)
    
    # RDF/OWL ontology definition
    ontology = """
@prefix : <http://kg-demo.org/stock#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Classes
:Company a owl:Class ;
    rdfs:label "Company" ;
    rdfs:comment "A publicly traded company" .

:PriceDay a owl:Class ;
    rdfs:label "Price Day" ;
    rdfs:comment "A trading day with price data" .

:Year a owl:Class ;
    rdfs:label "Year" ;
    rdfs:comment "A calendar year" .

:Quarter a owl:Class ;
    rdfs:label "Quarter" ;
    rdfs:comment "A fiscal quarter" .

:Month a owl:Class ;
    rdfs:label "Month" ;
    rdfs:comment "A calendar month" .

# Properties
:symbol a owl:DatatypeProperty ;
    rdfs:domain :Company ;
    rdfs:range xsd:string ;
    rdfs:label "Symbol" ;
    rdfs:comment "Stock ticker symbol" .

:date a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:date ;
    rdfs:label "Date" .

:open a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float ;
    rdfs:label "Opening Price" .

:high a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float ;
    rdfs:label "High Price" .

:low a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float ;
    rdfs:label "Low Price" .

:close a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float ;
    rdfs:label "Closing Price" .

:adj_close a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float ;
    rdfs:label "Adjusted Closing Price" .

:volume a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:integer ;
    rdfs:label "Trading Volume" .

:year a owl:DatatypeProperty ;
    rdfs:domain :Year ;
    rdfs:range xsd:integer ;
    rdfs:label "Year" .

# Object Properties (Relationships)
:hasPrice a owl:ObjectProperty ;
    rdfs:domain :Company ;
    rdfs:range :PriceDay ;
    rdfs:label "Has Price" ;
    rdfs:comment "Company has price data for a day" .

:correlatedWith a owl:ObjectProperty ;
    rdfs:domain :Company ;
    rdfs:range :Company ;
    rdfs:label "Correlated With" ;
    rdfs:comment "Companies with correlated price movements" .

:performedIn a owl:ObjectProperty ;
    rdfs:domain :Company ;
    rdfs:range :Year ;
    rdfs:label "Performed In" ;
    rdfs:comment "Company performance in a year" .

:inYear a owl:ObjectProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range :Year ;
    rdfs:label "In Year" .

:inQuarter a owl:ObjectProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range :Quarter ;
    rdfs:label "In Quarter" .

:inMonth a owl:ObjectProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range :Month ;
    rdfs:label "In Month" .
"""
    
    print("\n📋 Generated RDF/OWL Ontology:")
    print(ontology[:500] + "...")
    
    return ontology

def explore_n10s_usage():
    """Explore how to use n10s with existing data."""
    print("\n" + "=" * 60)
    print("N10S USAGE EXPLORATION")
    print("=" * 60)
    
    print("\n1️⃣  Import RDF/OWL Ontology:")
    print("   CALL n10s.onto.import.fetch('file:///path/to/ontology.ttl', 'Turtle')")
    
    print("\n2️⃣  Map Neo4j to RDF:")
    print("   CALL n10s.mapping.add('Company', 'http://kg-demo.org/stock#Company')")
    print("   CALL n10s.mapping.add('PriceDay', 'http://kg-demo.org/stock#PriceDay')")
    
    print("\n3️⃣  Export Neo4j data as RDF:")
    print("   CALL n10s.rdf.export.fetch('http://localhost:7474/rdf/cypher', 'Turtle')")
    
    print("\n4️⃣  Query using SPARQL:")
    print("   CALL n10s.query.sparql('SELECT ?company WHERE { ?company a :Company }')")
    
    print("\n5️⃣  Governance Benefits:")
    print("   • Schema validation against ontology")
    print("   • Type checking (Company, PriceDay, etc.)")
    print("   • Property constraints (date must be xsd:date)")
    print("   • Relationship validation (only defined properties allowed)")

def create_ontology_file():
    """Create ontology file for n10s."""
    ontology_content = """@prefix : <http://kg-demo.org/stock#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:Company a owl:Class ;
    rdfs:label "Company" ;
    rdfs:comment "A publicly traded company" .

:PriceDay a owl:Class ;
    rdfs:label "Price Day" ;
    rdfs:comment "A trading day with price data" .

:Year a owl:Class ;
    rdfs:label "Year" .

:Quarter a owl:Class ;
    rdfs:label "Quarter" .

:Month a owl:Class ;
    rdfs:label "Month" .

:symbol a owl:DatatypeProperty ;
    rdfs:domain :Company ;
    rdfs:range xsd:string .

:date a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:date .

:open a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float .

:high a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float .

:low a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float .

:close a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float .

:adj_close a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:float .

:volume a owl:DatatypeProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range xsd:integer .

:year a owl:DatatypeProperty ;
    rdfs:domain :Year ;
    rdfs:range xsd:integer .

:hasPrice a owl:ObjectProperty ;
    rdfs:domain :Company ;
    rdfs:range :PriceDay ;
    rdfs:label "Has Price" .

:correlatedWith a owl:ObjectProperty ;
    rdfs:domain :Company ;
    rdfs:range :Company ;
    rdfs:label "Correlated With" .

:performedIn a owl:ObjectProperty ;
    rdfs:domain :Company ;
    rdfs:range :Year ;
    rdfs:label "Performed In" .

:inYear a owl:ObjectProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range :Year .

:inQuarter a owl:ObjectProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range :Quarter .

:inMonth a owl:ObjectProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range :Month .
"""
    
    file_path = "/Users/adarshvuppala/kg_demo/chatbot/backend/stock_ontology.ttl"
    with open(file_path, 'w') as f:
        f.write(ontology_content)
    
    print(f"\n✅ Ontology file created: {file_path}")
    return file_path

def main():
    """Main exploration function."""
    print("\n" + "=" * 60)
    print("N10S & ONTOLOGY EXPLORATION")
    print("=" * 60)
    
    # Check n10s
    has_n10s = check_n10s()
    
    # Create ontology
    ontology = create_stock_ontology_rdf()
    ontology_file = create_ontology_file()
    
    # Explore usage
    explore_n10s_usage()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    if not has_n10s:
        print("1. Install n10s plugin in Neo4j")
        print("2. Restart Neo4j")
    print(f"3. Import ontology: CALL n10s.onto.import.fetch('file://{ontology_file}', 'Turtle')")
    print("4. Map existing nodes to RDF classes")
    print("5. Enable governance checks")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

