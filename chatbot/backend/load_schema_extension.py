#!/usr/bin/env python3
"""
Load Extended Neo4j Schema
===========================
This script extends the base Neo4j schema with time dimensions and derived
relationships for advanced GraphRAG queries.

Run this AFTER the base Company/PriceDay data is loaded.
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def load_schema_extension():
    """Load the extended schema from schema_extension.cypher file."""
    
    if not NEO4J_PASSWORD:
        logger.error("NEO4J_PASSWORD not set in environment")
        return False
    
    # Read the Cypher script
    script_path = os.path.join(os.path.dirname(__file__), "schema_extension.cypher")
    
    if not os.path.exists(script_path):
        logger.error(f"Schema extension file not found: {script_path}")
        return False
    
    with open(script_path, 'r') as f:
        cypher_script = f.read()
    
    # Split into individual statements (separated by semicolons)
    # Better parsing: split by semicolon, then clean each statement
    statements = []
    current_statement = []
    
    for line in cypher_script.split('\n'):
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith('//'):
            continue
        
        # Add line to current statement
        current_statement.append(line)
        
        # If line ends with semicolon, finalize statement
        if line.endswith(';'):
            statement = ' '.join(current_statement).rstrip(';').strip()
            if statement and not statement.startswith('//'):
                statements.append(statement)
            current_statement = []
    
    # Handle any remaining statement without semicolon
    if current_statement:
        statement = ' '.join(current_statement).strip()
        if statement and not statement.startswith('//'):
            statements.append(statement)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            logger.info("Starting schema extension...")
            
            for i, statement in enumerate(statements, 1):
                if not statement or statement.startswith('//'):
                    continue
                
                try:
                    logger.info(f"Executing statement {i}/{len(statements)}...")
                    result = session.run(statement)
                    
                    # Consume result to execute
                    records = list(result)
                    
                    # Log summary if available
                    if records:
                        logger.info(f"  Result: {records[0].data() if records else 'OK'}")
                    
                except Exception as e:
                    logger.error(f"Error executing statement {i}: {str(e)}")
                    logger.error(f"Statement: {statement[:100]}...")
                    # Continue with next statement
                    continue
            
            logger.info("Schema extension completed!")
            return True
            
    except Exception as e:
        logger.error(f"Failed to load schema extension: {str(e)}")
        return False
    finally:
        driver.close()

def verify_schema():
    """Verify that the extended schema was loaded correctly."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Check node counts
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS node_type, COUNT(n) AS count
                ORDER BY count DESC
            """)
            
            logger.info("\nNode counts:")
            for record in result:
                logger.info(f"  {record['node_type']}: {record['count']}")
            
            # Check relationship counts
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS rel_type, COUNT(r) AS count
                ORDER BY count DESC
            """)
            
            logger.info("\nRelationship counts:")
            for record in result:
                logger.info(f"  {record['rel_type']}: {record['count']}")
            
            # Check for time dimensions
            result = session.run("MATCH (y:Year) RETURN COUNT(y) AS count")
            year_count = result.single()["count"]
            
            result = session.run("MATCH (q:Quarter) RETURN COUNT(q) AS count")
            quarter_count = result.single()["count"]
            
            result = session.run("MATCH (m:Month) RETURN COUNT(m) AS count")
            month_count = result.single()["count"]
            
            logger.info(f"\nTime dimensions:")
            logger.info(f"  Years: {year_count}")
            logger.info(f"  Quarters: {quarter_count}")
            logger.info(f"  Months: {month_count}")
            
            if year_count > 0 and quarter_count > 0 and month_count > 0:
                logger.info("\n✓ Schema extension verified successfully!")
                return True
            else:
                logger.warning("\n⚠ Some time dimensions are missing")
                return False
                
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return False
    finally:
        driver.close()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Neo4j Schema Extension Loader")
    logger.info("=" * 60)
    
    if load_schema_extension():
        logger.info("\nVerifying schema...")
        verify_schema()
    else:
        logger.error("Schema extension failed. Please check errors above.")

