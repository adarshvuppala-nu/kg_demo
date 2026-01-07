#!/usr/bin/env python3
"""
Explore Ontop VKG (Virtual Knowledge Graph)
===========================================
Explores how to use Ontop to create a Virtual Knowledge Graph from PostgreSQL.

Based on:
- PostgreSQL database: kg_demo
- Table: stock_prices
- Columns: date, open, high, low, close, adj_close, volume, symbol
"""

import os
import subprocess
from pathlib import Path

def find_ontop():
    """Find Ontop installation."""
    print("=" * 60)
    print("FINDING ONTOP INSTALLATION")
    print("=" * 60)
    
    ontop_dir = Path("/Users/adarshvuppala/kg_demo/ontop")
    
    # Look for ontop CLI
    possible_paths = [
        ontop_dir / "ontop-tutorial" / "endpoint" / "ontop-cli",
        ontop_dir / "ontop",
        ontop_dir / "ontop-tutorial" / "ontop",
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"\n✅ Found Ontop at: {path}")
            return path
    
    print("\n⚠️  Ontop CLI not found in expected locations")
    print("   Checking ontop-tutorial structure...")
    
    tutorial_dir = ontop_dir / "ontop-tutorial"
    if tutorial_dir.exists():
        print(f"   Tutorial directory exists: {tutorial_dir}")
        for item in tutorial_dir.iterdir():
            if item.is_dir():
                print(f"      - {item.name}/")
    
    return None

def create_ontop_mapping():
    """Create Ontop mapping file (OBDA) for stock data."""
    print("\n" + "=" * 60)
    print("CREATING ONTOP MAPPING (OBDA)")
    print("=" * 60)
    
    # OBDA mapping file for stock_prices table
    obda_content = """[PrefixDeclaration]
:	http://kg-demo.org/stock#
rdf:	http://www.w3.org/1999/02/22-rdf-syntax-ns#
rdfs:	http://www.w3.org/2000/01/rdf-schema#
owl:	http://www.w3.org/2002/07/owl#
xsd:	http://www.w3.org/2001/XMLSchema#

[MappingDeclaration] @collection [[

mappingId	stock_prices_company
target		:Company_{symbol} a :Company ; :symbol "{symbol}"^^xsd:string .
source		SELECT symbol FROM stock_prices GROUP BY symbol

mappingId	stock_prices_priceday
target		:PriceDay_{date}_{symbol} a :PriceDay ;
			:date "{date}"^^xsd:date ;
			:open {open}^^xsd:float ;
			:high {high}^^xsd:float ;
			:low {low}^^xsd:float ;
			:close {close}^^xsd:float ;
			:adj_close {adj_close}^^xsd:float ;
			:volume {volume}^^xsd:integer ;
			:hasCompany :Company_{symbol} .
source		SELECT date, open, high, low, close, adj_close, volume, symbol 
			FROM stock_prices

]]"""
    
    obda_file = "/Users/adarshvuppala/kg_demo/chatbot/backend/stock_mapping.obda"
    with open(obda_file, 'w') as f:
        f.write(obda_content)
    
    print(f"\n✅ OBDA mapping file created: {obda_file}")
    return obda_file

def create_ontop_ontology():
    """Create Ontop-compatible ontology."""
    print("\n" + "=" * 60)
    print("CREATING ONTOP ONTOLOGY (OWL)")
    print("=" * 60)
    
    ontology_content = """@prefix : <http://kg-demo.org/stock#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:Company a owl:Class ;
    rdfs:label "Company" .

:PriceDay a owl:Class ;
    rdfs:label "Price Day" .

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

:hasCompany a owl:ObjectProperty ;
    rdfs:domain :PriceDay ;
    rdfs:range :Company .
"""
    
    ontology_file = "/Users/adarshvuppala/kg_demo/chatbot/backend/stock_ontology_ontop.owl"
    with open(ontology_file, 'w') as f:
        f.write(ontology_content)
    
    print(f"\n✅ Ontology file created: {ontology_file}")
    return ontology_file

def create_ontop_properties():
    """Create Ontop properties file."""
    print("\n" + "=" * 60)
    print("CREATING ONTOP PROPERTIES FILE")
    print("=" * 60)
    
    properties_content = """jdbc.url=jdbc:postgresql://localhost:5434/kg_demo
jdbc.user=postgres
jdbc.password=postgres
jdbc.driver=org.postgresql.Driver

ontologyFile=stock_ontology_ontop.owl
mappingFile=stock_mapping.obda
"""
    
    properties_file = "/Users/adarshvuppala/kg_demo/chatbot/backend/stock_ontop.properties"
    with open(properties_file, 'w') as f:
        f.write(properties_content)
    
    print(f"\n✅ Properties file created: {properties_file}")
    return properties_file

def show_ontop_usage():
    """Show how to use Ontop."""
    print("\n" + "=" * 60)
    print("ONTOP USAGE")
    print("=" * 60)
    
    print("\n1️⃣  Start Ontop Endpoint:")
    print("   ontop endpoint --mapping=stock_mapping.obda --ontology=stock_ontology_ontop.owl --properties=stock_ontop.properties")
    
    print("\n2️⃣  Query with SPARQL:")
    print("   PREFIX : <http://kg-demo.org/stock#>")
    print("   SELECT ?company ?symbol WHERE {")
    print("     ?company a :Company .")
    print("     ?company :symbol ?symbol .")
    print("   }")
    
    print("\n3️⃣  Benefits:")
    print("   • Virtual Knowledge Graph - no data duplication")
    print("   • SPARQL queries over PostgreSQL")
    print("   • Ontology-based governance")
    print("   • RDF/OWL compliance")
    print("   • Works with existing PostgreSQL data")

def main():
    """Main exploration."""
    print("\n" + "=" * 60)
    print("ONTOP VKG EXPLORATION")
    print("=" * 60)
    
    ontop_path = find_ontop()
    
    obda_file = create_ontop_mapping()
    ontology_file = create_ontop_ontology()
    properties_file = create_ontop_properties()
    
    show_ontop_usage()
    
    print("\n" + "=" * 60)
    print("FILES CREATED:")
    print("=" * 60)
    print(f"   • {obda_file}")
    print(f"   • {ontology_file}")
    print(f"   • {properties_file}")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

