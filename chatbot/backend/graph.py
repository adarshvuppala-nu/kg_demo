from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Create driver with connection pooling and optimizations
driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
    max_connection_lifetime=3600,  # 1 hour
    max_connection_pool_size=50,  # Connection pooling
    connection_acquisition_timeout=30  # Timeout for getting connections
)

def run_cypher(query: str, params: Optional[dict] = None, read_only: bool = True):
    """
    Executes a Cypher query and returns records as a list of dicts.
    Production-ready with connection pooling, error handling, and retry logic.
    
    Args:
        query: Cypher query string
        params: Query parameters dictionary
        read_only: If True, uses read transaction (default: True)
    
    Returns:
        List of dictionaries (record.data() for each record)
    """
    if not query or not query.strip():
        logger.error("Empty query provided")
        return []
    
    try:
        with driver.session() as session:
            def execute_query(tx):
                try:
                    result = tx.run(query, params or {})
                    # Consume result within transaction
                    records = [record.data() for record in result]
                    return records
                except Exception as e:
                    logger.error(f"Transaction error: {str(e)}")
                    raise
            
            if read_only:
                records = session.read_transaction(execute_query)
            else:
                records = session.write_transaction(execute_query)
            
            return records if records else []
    except Exception as e:
        logger.error(f"Cypher query failed: {str(e)}")
        logger.error(f"Query: {query[:200]}...")
        logger.error(f"Params: {params}")
        # Don't raise - return empty list for graceful handling
        return []

def validate_schema_connection() -> bool:
    """
    Validate that Neo4j connection is working and schema exists.
    Returns True if connection is valid and basic nodes exist.
    """
    try:
        with driver.session() as session:
            result = session.run("MATCH (c:Company) RETURN COUNT(c) AS count LIMIT 1")
            record = result.single()
            if record and record["count"] > 0:
                logger.info(f"Schema validated: {record['count']} Company nodes found")
                return True
            else:
                logger.warning("Schema validation: No Company nodes found")
                return False
    except Exception as e:
        logger.error(f"Schema validation failed: {str(e)}")
        return False

def close_driver():
    """Close the driver connection (useful for cleanup)."""
    if driver:
        driver.close()
