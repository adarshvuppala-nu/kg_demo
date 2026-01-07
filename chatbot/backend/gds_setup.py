#!/usr/bin/env python3
"""
Neo4j Graph Data Science (GDS) Setup
=====================================
Production-ready GDS implementation for GraphRAG system.

This script creates:
1. GDS projection: 'company-graph'
2. Node Similarity: GDS_SIMILAR relationships
3. PageRank: Company.pagerank property
4. Louvain Community Detection: Company.community property
5. FastRP Embeddings: Company.embedding property (128-dim)

All operations are ADDITIVE and IDEMPOTENT - safe to run multiple times.

Usage:
    python gds_setup.py

Requirements:
    - Neo4j with GDS plugin installed
    - CORRELATED_WITH relationships must exist
    - Company nodes must exist
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv('/Users/adarshvuppala/kg_demo/.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# GDS Configuration
GDS_CONFIG = {
    "projection_name": "company-graph",
    "node_similarity": {
        "writeRelationshipType": "GDS_SIMILAR",
        "writeProperty": "score",
        "similarityCutoff": 0.1,
        "topK": 5
    },
    "pagerank": {
        "maxIterations": 20,
        "dampingFactor": 0.85,
        "relationshipWeightProperty": "correlation",
        "writeProperty": "pagerank"
    },
    "louvain": {
        "writeProperty": "community",
        "relationshipWeightProperty": "correlation"
    },
    "fastrp": {
        "embeddingDimension": 128,
        "iterationWeights": [0.0, 1.0, 1.0],
        "relationshipWeightProperty": "correlation",
        "writeProperty": "embedding"
    }
}


class GDSSetup:
    """Production-ready GDS setup manager."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.config = GDS_CONFIG
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()
    
    def verify_gds(self) -> bool:
        """Verify GDS is installed and available."""
        try:
            with self.driver.session() as session:
                result = session.run("CALL gds.version()")
                record = result.single()
                if record:
                    version = record.get('gdsVersion') or list(record.values())[0]
                    logger.info(f"✅ GDS Version: {version}")
                    return True
        except Exception as e:
            logger.error(f"❌ GDS not available: {str(e)}")
            logger.error("\nGDS Installation Required:")
            logger.error("  - Neo4j Enterprise: GDS included")
            logger.error("  - Neo4j Desktop: Install GDS plugin")
            logger.error("  - Neo4j Community: Add GDS library manually")
            return False
        return False
    
    def verify_prerequisites(self) -> bool:
        """Verify required nodes and relationships exist."""
        try:
            with self.driver.session() as session:
                # Check Company nodes
                result = session.run("MATCH (c:Company) RETURN COUNT(c) AS count")
                company_count = result.single()["count"]
                if company_count == 0:
                    logger.error("❌ No Company nodes found. Load data first.")
                    return False
                logger.info(f"✅ Found {company_count} Company nodes")
                
                # Check CORRELATED_WITH relationships
                result = session.run("MATCH ()-[r:CORRELATED_WITH]-() RETURN COUNT(r) AS count")
                corr_count = result.single()["count"]
                if corr_count == 0:
                    logger.warning("⚠️  No CORRELATED_WITH relationships found.")
                    logger.warning("   Run: python load_schema_extension.py first")
                    return False
                logger.info(f"✅ Found {corr_count} CORRELATED_WITH relationships")
                return True
        except Exception as e:
            logger.error(f"❌ Prerequisites check failed: {str(e)}")
            return False
    
    def create_projection(self) -> bool:
        """Create or recreate GDS projection (idempotent)."""
        try:
            with self.driver.session() as session:
                # Drop existing projection if it exists (idempotent)
                try:
                    session.run(
                        f"CALL gds.graph.drop('{self.config['projection_name']}', false) YIELD graphName",
                        read_transaction=False
                    )
                    logger.info("   Dropped existing projection (if any)")
                except:
                    pass  # Projection doesn't exist, which is fine
                
                # Create projection
                query = f"""
                CALL gds.graph.project(
                    '{self.config['projection_name']}',
                    'Company',
                    {{
                        CORRELATED_WITH: {{
                            type: 'CORRELATED_WITH',
                            orientation: 'UNDIRECTED',
                            properties: {{
                                correlation: {{
                                    property: 'correlation',
                                    defaultValue: 0.0
                                }}
                            }}
                        }}
                    }},
                    {{}}
                )
                YIELD graphName, nodeCount, relationshipCount
                RETURN graphName, nodeCount, relationshipCount
                """
                
                result = session.run(query)
                record = result.single()
                
                if record:
                    logger.info(f"✅ Projection created: {record['graphName']}")
                    logger.info(f"   Nodes: {record['nodeCount']}")
                    logger.info(f"   Relationships: {record['relationshipCount']}")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Projection creation failed: {str(e)}")
            return False
    
    def run_node_similarity(self) -> bool:
        """Run Node Similarity algorithm (idempotent)."""
        try:
            with self.driver.session() as session:
                config = self.config['node_similarity']
                query = f"""
                CALL gds.nodeSimilarity.write(
                    '{self.config['projection_name']}',
                    {{
                        writeRelationshipType: '{config['writeRelationshipType']}',
                        writeProperty: '{config['writeProperty']}',
                        similarityCutoff: {config['similarityCutoff']},
                        topK: {config['topK']}
                    }}
                )
                YIELD nodesCompared, relationshipsWritten
                RETURN nodesCompared, relationshipsWritten
                """
                
                result = session.run(query)
                record = result.single()
                
                if record:
                    logger.info(f"✅ Node Similarity completed")
                    logger.info(f"   Nodes compared: {record['nodesCompared']}")
                    logger.info(f"   Relationships written: {record['relationshipsWritten']}")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Node Similarity failed: {str(e)}")
            return False
    
    def run_pagerank(self) -> bool:
        """Run PageRank algorithm (idempotent)."""
        try:
            with self.driver.session() as session:
                config = self.config['pagerank']
                query = f"""
                CALL gds.pageRank.write(
                    '{self.config['projection_name']}',
                    {{
                        maxIterations: {config['maxIterations']},
                        dampingFactor: {config['dampingFactor']},
                        relationshipWeightProperty: '{config['relationshipWeightProperty']}',
                        writeProperty: '{config['writeProperty']}'
                    }}
                )
                YIELD nodePropertiesWritten, ranIterations, didConverge
                RETURN nodePropertiesWritten, ranIterations, didConverge
                """
                
                result = session.run(query)
                record = result.single()
                
                if record:
                    logger.info(f"✅ PageRank completed")
                    logger.info(f"   Properties written: {record['nodePropertiesWritten']}")
                    logger.info(f"   Iterations: {record['ranIterations']}")
                    logger.info(f"   Converged: {record['didConverge']}")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ PageRank failed: {str(e)}")
            return False
    
    def run_louvain(self) -> bool:
        """Run Louvain community detection (idempotent)."""
        try:
            with self.driver.session() as session:
                config = self.config['louvain']
                query = f"""
                CALL gds.louvain.write(
                    '{self.config['projection_name']}',
                    {{
                        writeProperty: '{config['writeProperty']}',
                        relationshipWeightProperty: '{config['relationshipWeightProperty']}'
                    }}
                )
                YIELD communityCount, ranLevels, modularity
                RETURN communityCount, ranLevels, modularity
                """
                
                result = session.run(query)
                record = result.single()
                
                if record:
                    logger.info(f"✅ Louvain Community Detection completed")
                    logger.info(f"   Communities found: {record['communityCount']}")
                    logger.info(f"   Levels: {record['ranLevels']}")
                    logger.info(f"   Modularity: {record['modularity']:.4f}")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Louvain failed: {str(e)}")
            return False
    
    def run_fastrp(self) -> bool:
        """Run FastRP embeddings (idempotent, optional)."""
        try:
            with self.driver.session() as session:
                config = self.config['fastrp']
                query = f"""
                CALL gds.fastRP.write(
                    '{self.config['projection_name']}',
                    {{
                        embeddingDimension: {config['embeddingDimension']},
                        iterationWeights: {config['iterationWeights']},
                        relationshipWeightProperty: '{config['relationshipWeightProperty']}',
                        writeProperty: '{config['writeProperty']}'
                    }}
                )
                YIELD nodePropertiesWritten
                RETURN nodePropertiesWritten
                """
                
                result = session.run(query)
                record = result.single()
                
                if record:
                    logger.info(f"✅ FastRP Embeddings created")
                    logger.info(f"   Properties written: {record['nodePropertiesWritten']}")
                    logger.info(f"   Embedding dimension: {config['embeddingDimension']}")
                    return True
                return False
        except Exception as e:
            logger.warning(f"⚠️  FastRP Embeddings failed (optional): {str(e)}")
            return False
    
    def verify_results(self) -> Dict[str, Any]:
        """Comprehensive verification of all GDS outputs."""
        results = {}
        
        try:
            with self.driver.session() as session:
                # Verify projection
                result = session.run(
                    f"CALL gds.graph.list() YIELD graphName WHERE graphName = '{self.config['projection_name']}' RETURN graphName"
                )
                results['projection'] = result.single() is not None
                
                # Verify Node Similarity
                result = session.run("MATCH ()-[r:GDS_SIMILAR]-() RETURN COUNT(r) AS count")
                results['node_similarity'] = result.single()["count"]
                
                # Verify PageRank
                result = session.run("MATCH (c:Company) WHERE c.pagerank IS NOT NULL RETURN COUNT(c) AS count")
                results['pagerank'] = result.single()["count"]
                
                # Verify Community
                result = session.run("MATCH (c:Company) WHERE c.community IS NOT NULL RETURN COUNT(c) AS count")
                results['community'] = result.single()["count"]
                
                # Verify Embeddings
                result = session.run("MATCH (c:Company) WHERE c.embedding IS NOT NULL RETURN COUNT(c) AS count")
                results['embeddings'] = result.single()["count"]
                
                # Sample queries
                logger.info("\n📊 Verification Results:")
                logger.info(f"   Projection exists: {results['projection']}")
                logger.info(f"   GDS_SIMILAR relationships: {results['node_similarity']}")
                logger.info(f"   Companies with PageRank: {results['pagerank']}")
                logger.info(f"   Companies with Community: {results['community']}")
                logger.info(f"   Companies with Embeddings: {results['embeddings']}")
                
                # Top PageRank companies
                result = session.run("""
                    MATCH (c:Company)
                    WHERE c.pagerank IS NOT NULL
                    RETURN c.symbol, c.pagerank
                    ORDER BY c.pagerank DESC
                    LIMIT 5
                """)
                logger.info("\n   Top PageRank companies:")
                for record in result:
                    logger.info(f"      {record['c.symbol']}: {record['c.pagerank']:.6f}")
                
                # Community distribution
                result = session.run("""
                    MATCH (c:Company)
                    WHERE c.community IS NOT NULL
                    WITH c.community AS community, COLLECT(c.symbol) AS companies, COUNT(c) AS size
                    RETURN community, size, companies
                    ORDER BY size DESC
                """)
                logger.info("\n   Community distribution:")
                for record in result:
                    logger.info(f"      Community {record['community']}: {record['size']} companies - {record['companies']}")
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {str(e)}")
        
        return results
    
    def run_all(self) -> bool:
        """Run all GDS algorithms in sequence."""
        logger.info("=" * 60)
        logger.info("Neo4j Graph Data Science (GDS) Setup")
        logger.info("=" * 60)
        
        # Step 1: Verify GDS
        if not self.verify_gds():
            return False
        
        # Step 2: Verify prerequisites
        if not self.verify_prerequisites():
            return False
        
        # Step 3: Create projection
        logger.info("\n[Step 1] Creating GDS Projection...")
        if not self.create_projection():
            return False
        
        # Step 4: Run algorithms
        steps = [
            ("Node Similarity", self.run_node_similarity),
            ("PageRank", self.run_pagerank),
            ("Louvain Community Detection", self.run_louvain),
            ("FastRP Embeddings", self.run_fastrp),
        ]
        
        results = {}
        for step_name, step_func in steps:
            logger.info(f"\n[Step {steps.index((step_name, step_func)) + 2}] Running {step_name}...")
            try:
                results[step_name] = step_func()
            except Exception as e:
                logger.error(f"Error in {step_name}: {str(e)}")
                results[step_name] = False
        
        # Step 5: Verify results
        logger.info("\n[Step 6] Verifying Results...")
        verification = self.verify_results()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("GDS Setup Summary")
        logger.info("=" * 60)
        for step_name, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {step_name}")
        
        all_success = all(results.values())
        if all_success:
            logger.info("\n✅ All GDS operations completed successfully!")
        else:
            logger.warning("\n⚠️  Some operations failed. Check logs above.")
        
        return all_success


def main():
    """Main entry point."""
    if not NEO4J_PASSWORD:
        logger.error("NEO4J_PASSWORD not set in environment")
        return False
    
    with GDSSetup(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) as gds:
        return gds.run_all()


if __name__ == "__main__":
    main()
