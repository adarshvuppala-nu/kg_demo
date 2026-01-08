#!/usr/bin/env python3
"""
Load Companies Data from Postgres to Neo4j
==========================================
Loads company metadata (sector, location, employees, market cap) from Postgres
and enriches existing Company nodes in Neo4j.

This script:
1. Connects to Postgres and reads companies table
2. Enriches existing Company nodes with additional properties
3. Creates Sector, Country, City, State nodes
4. Creates relationships: IN_SECTOR, LOCATED_IN, IN_COUNTRY, IN_STATE, IN_CITY
5. Creates indexes for efficient queries
"""

import os
import psycopg2
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging
from typing import Optional

# Load from root .env
load_dotenv('/Users/adarshvuppala/kg_demo/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Postgres connection
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5434")
PG_DB = os.getenv("PG_DB", "kg_demo")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres123")

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test12345")

def load_companies_from_postgres():
    """Load companies data from Postgres."""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()
        
        # Get all companies
        cursor.execute("""
            SELECT 
                symbol, 
                sector, 
                country, 
                city, 
                state,
                fulltimeemployees,
                marketcap
            FROM companies
            ORDER BY symbol
        """)
        
        companies = []
        for row in cursor.fetchall():
            companies.append({
                'symbol': row[0],
                'sector': row[1],
                'country': row[2],
                'city': row[3],
                'state': row[4],
                'fulltimeemployees': row[5],
                'marketcap': row[6]
            })
        
        cursor.close()
        conn.close()
        
        logger.info(f"Loaded {len(companies)} companies from Postgres")
        return companies
        
    except Exception as e:
        logger.error(f"Failed to load companies from Postgres: {str(e)}")
        return None

def create_constraints_and_indexes(driver):
    """Create constraints and indexes for new node types."""
    with driver.session() as session:
        logger.info("Creating constraints and indexes...")
        
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT sector_name IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT state_name IF NOT EXISTS FOR (s:State) REQUIRE (s.name, s.country) IS NODE KEY",
            "CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE (c.name, c.state, c.country) IS NODE KEY",
        ]
        
        for constraint in constraints:
            try:
                session.run(constraint)
                logger.info(f"  ✓ {constraint[:50]}...")
            except Exception as e:
                if "already exists" in str(e).lower() or "equivalent constraint" in str(e).lower():
                    logger.info(f"  ⊙ Constraint already exists")
                else:
                    logger.warning(f"  ⚠ {str(e)[:80]}")
        
        # Create indexes
        indexes = [
            "CREATE INDEX sector_name_idx IF NOT EXISTS FOR (s:Sector) ON (s.name)",
            "CREATE INDEX country_name_idx IF NOT EXISTS FOR (c:Country) ON (c.name)",
            "CREATE INDEX company_sector_idx IF NOT EXISTS FOR (c:Company) ON (c.sector)",
        ]
        
        for index in indexes:
            try:
                session.run(index)
                logger.info(f"  ✓ {index[:50]}...")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"  ⊙ Index already exists")
                else:
                    logger.warning(f"  ⚠ {str(e)[:80]}")

def load_companies_to_neo4j(companies):
    """Load companies data into Neo4j."""
    if not companies:
        logger.error("No companies data to load")
        return False
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Step 1: Create Sector nodes
            logger.info("\nStep 1: Creating Sector nodes...")
            sectors = set(c['sector'] for c in companies if c['sector'])
            
            for sector in sectors:
                session.run(
                    "MERGE (s:Sector {name: $sector})",
                    {"sector": sector}
                )
            logger.info(f"  ✓ Created {len(sectors)} Sector nodes")
            
            # Step 2: Create Country nodes
            logger.info("\nStep 2: Creating Country nodes...")
            countries = set(c['country'] for c in companies if c['country'])
            
            for country in countries:
                session.run(
                    "MERGE (c:Country {name: $country})",
                    {"country": country}
                )
            logger.info(f"  ✓ Created {len(countries)} Country nodes")
            
            # Step 3: Create State nodes
            logger.info("\nStep 3: Creating State nodes...")
            states = set((c['state'], c['country']) for c in companies if c['state'] and c['country'])
            
            for state, country in states:
                session.run(
                    """
                    MERGE (s:State {name: $state, country: $country})
                    MERGE (c:Country {name: $country})
                    MERGE (s)-[:IN_COUNTRY]->(c)
                    """,
                    {"state": state, "country": country}
                )
            logger.info(f"  ✓ Created {len(states)} State nodes")
            
            # Step 4: Create City nodes
            logger.info("\nStep 4: Creating City nodes...")
            cities = set((c['city'], c['state'], c['country']) 
                        for c in companies if c['city'] and c['state'] and c['country'])
            
            for city, state, country in cities:
                session.run(
                    """
                    MERGE (ci:City {name: $city, state: $state, country: $country})
                    MERGE (s:State {name: $state, country: $country})
                    MERGE (ci)-[:IN_STATE]->(s)
                    """,
                    {"city": city, "state": state, "country": country}
                )
            logger.info(f"  ✓ Created {len(cities)} City nodes")
            
            # Step 5: Enrich Company nodes and create relationships
            logger.info("\nStep 5: Enriching Company nodes and creating relationships...")
            batch_size = 100
            total = len(companies)
            
            for i in range(0, total, batch_size):
                batch = companies[i:i+batch_size]
                
                for company in batch:
                    symbol = company['symbol']
                    sector = company.get('sector')
                    country = company.get('country')
                    city = company.get('city')
                    state = company.get('state')
                    employees = company.get('fulltimeemployees')
                    marketcap = company.get('marketcap')
                    
                    # Build query to update Company and create relationships
                    query_parts = ["MATCH (c:Company {symbol: $symbol})"]
                    params = {"symbol": symbol}
                    
                    # Update Company properties
                    updates = []
                    if sector:
                        updates.append("c.sector = $sector")
                        params['sector'] = sector
                    if employees is not None:
                        updates.append("c.fulltimeemployees = $employees")
                        params['employees'] = int(employees)
                    if marketcap is not None:
                        updates.append("c.marketcap = $marketcap")
                        params['marketcap'] = float(marketcap)
                    
                    if updates:
                        query_parts.append(f"SET {', '.join(updates)}")
                    
                    # Create relationships - only add to query if we have the data
                    if sector:
                        query_parts.append("MERGE (s:Sector {name: $sector})")
                        query_parts.append("MERGE (c)-[:IN_SECTOR]->(s)")
                    
                    if country:
                        query_parts.append("MERGE (co:Country {name: $country})")
                        query_parts.append("MERGE (c)-[:LOCATED_IN]->(co)")
                        params['country'] = country
                    
                    if state and country:
                        query_parts.append("MERGE (st:State {name: $state, country: $country})")
                        query_parts.append("MERGE (c)-[:IN_STATE]->(st)")
                        params['state'] = state
                    
                    if city and state and country:
                        query_parts.append("MERGE (ci:City {name: $city, state: $state, country: $country})")
                        query_parts.append("MERGE (c)-[:IN_CITY]->(ci)")
                        params['city'] = city
                    
                    query = "\n".join(query_parts)
                    session.run(query, params)
                
                if (i + batch_size) % 500 == 0 or (i + batch_size) >= total:
                    logger.info(f"  ✓ Processed {min(i + batch_size, total)}/{total} companies")
            
            logger.info(f"  ✓ Enriched {total} Company nodes")
            
            # Step 6: Verify counts
            logger.info("\nStep 6: Verifying data...")
            result = session.run("MATCH (c:Company) WHERE c.sector IS NOT NULL RETURN COUNT(c) AS count")
            companies_with_sector = result.single()["count"]
            
            result = session.run("MATCH (s:Sector) RETURN COUNT(s) AS count")
            sector_count = result.single()["count"]
            
            result = session.run("MATCH (c:Company)-[:IN_SECTOR]->(s:Sector) RETURN COUNT(*) AS count")
            sector_rels = result.single()["count"]
            
            logger.info(f"  ✓ Companies with sector: {companies_with_sector}")
            logger.info(f"  ✓ Sector nodes: {sector_count}")
            logger.info(f"  ✓ IN_SECTOR relationships: {sector_rels}")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to load companies: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        driver.close()

def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Load Companies Data to Neo4j")
    logger.info("=" * 60)
    
    # Load from Postgres
    companies = load_companies_from_postgres()
    if not companies:
        logger.error("Failed to load companies from Postgres")
        return False
    
    # Create driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Create constraints and indexes
        create_constraints_and_indexes(driver)
        
        # Load companies to Neo4j
        if not load_companies_to_neo4j(companies):
            logger.error("Failed to load companies to Neo4j")
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Companies data loading completed successfully!")
        logger.info("=" * 60)
        logger.info("\nNew capabilities:")
        logger.info("  • Query companies by sector")
        logger.info("  • Find companies in same sector")
        logger.info("  • Sector-based GDS analysis")
        logger.info("  • Location-based queries")
        logger.info("  • Market cap and employee analysis")
        
        return True
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()

