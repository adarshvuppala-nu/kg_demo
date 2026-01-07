#!/usr/bin/env python3
"""
Load Stock Price Data into Neo4j
=================================
Loads Company and PriceDay nodes from CSV into Neo4j.

This script:
1. Reads stock_prices_pg.csv
2. Creates Company nodes (one per symbol)
3. Creates PriceDay nodes (one per date+symbol)
4. Creates HAS_PRICE relationships
5. Creates constraints and indexes
"""

import os
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging
from datetime import datetime

# Load from root .env
load_dotenv('/Users/adarshvuppala/kg_demo/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def create_constraints():
    """Create constraints and indexes."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            logger.info("Creating constraints and indexes...")
            
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT company_symbol IF NOT EXISTS FOR (c:Company) REQUIRE c.symbol IS UNIQUE",
                "CREATE CONSTRAINT priceday_date_symbol IF NOT EXISTS FOR (p:PriceDay) REQUIRE (p.date, p.symbol) IS NODE KEY",
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
                "CREATE INDEX company_symbol_idx IF NOT EXISTS FOR (c:Company) ON (c.symbol)",
                "CREATE INDEX priceday_date_idx IF NOT EXISTS FOR (p:PriceDay) ON (p.date)",
                "CREATE INDEX priceday_symbol_idx IF NOT EXISTS FOR (p:PriceDay) ON (p.symbol)",
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
                        
    except Exception as e:
        logger.error(f"Failed to create constraints: {str(e)}")
        return False
    finally:
        driver.close()
    
    return True

def load_data():
    """Load data from CSV into Neo4j."""
    
    if not NEO4J_PASSWORD:
        logger.error("NEO4J_PASSWORD not set in environment")
        return False
    
    # Find CSV file
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "rawdata_cleanupscripts",
        "stock_prices_pg.csv"
    )
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    logger.info(f"Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from CSV")
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Step 1: Create Company nodes
            logger.info("\nStep 1: Creating Company nodes...")
            symbols = df['symbol'].unique()
            
            for symbol in symbols:
                session.run(
                    "MERGE (c:Company {symbol: $symbol})",
                    {"symbol": symbol}
                )
            logger.info(f"  ✓ Created {len(symbols)} Company nodes: {list(symbols)}")
            
            # Step 2: Create PriceDay nodes and relationships in batches
            logger.info("\nStep 2: Creating PriceDay nodes and relationships...")
            batch_size = 1000
            total_rows = len(df)
            
            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i+batch_size]
                
                # Prepare batch data
                records = []
                for _, row in batch.iterrows():
                    records.append({
                        'symbol': row['symbol'],
                        'date': row['date'].strftime('%Y-%m-%d'),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'adj_close': float(row['adj_close']),
                        'volume': int(row['volume'])
                    })
                
                # Create PriceDay nodes and relationships
                query = """
                UNWIND $records AS record
                MATCH (c:Company {symbol: record.symbol})
                MERGE (p:PriceDay {date: date(record.date), symbol: record.symbol})
                SET p.open = record.open,
                    p.high = record.high,
                    p.low = record.low,
                    p.close = record.close,
                    p.adj_close = record.adj_close,
                    p.volume = record.volume
                MERGE (c)-[:HAS_PRICE]->(p)
                """
                
                session.run(query, {"records": records})
                
                if (i + batch_size) % 5000 == 0 or (i + batch_size) >= total_rows:
                    logger.info(f"  ✓ Processed {min(i + batch_size, total_rows)}/{total_rows} rows")
            
            logger.info(f"  ✓ Created {total_rows} PriceDay nodes and relationships")
            
            # Step 3: Verify counts
            logger.info("\nStep 3: Verifying data...")
            result = session.run("MATCH (c:Company) RETURN COUNT(c) AS count")
            company_count = result.single()["count"]
            
            result = session.run("MATCH (p:PriceDay) RETURN COUNT(p) AS count")
            priceday_count = result.single()["count"]
            
            result = session.run("MATCH (c:Company)-[:HAS_PRICE]->(p:PriceDay) RETURN COUNT(*) AS count")
            relationship_count = result.single()["count"]
            
            logger.info(f"  ✓ Company nodes: {company_count}")
            logger.info(f"  ✓ PriceDay nodes: {priceday_count}")
            logger.info(f"  ✓ HAS_PRICE relationships: {relationship_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        driver.close()

def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Neo4j Data Loader")
    logger.info("=" * 60)
    
    # Create constraints first
    if not create_constraints():
        logger.error("Failed to create constraints")
        return False
    
    # Load data
    if not load_data():
        logger.error("Failed to load data")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Data loading completed successfully!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("  1. Run: python load_schema_extension.py (creates time dimensions)")
    logger.info("  2. Run: python gds_setup.py (creates GDS analytics)")
    
    return True

if __name__ == "__main__":
    main()

