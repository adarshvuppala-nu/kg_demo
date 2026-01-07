// ============================================================================
// NEO4J GRAPH DATA SCIENCE (GDS) SETUP - PRODUCTION READY
// ============================================================================
// This script creates GDS analytics for the GraphRAG system.
// All operations are ADDITIVE and IDEMPOTENT - safe to run multiple times.
//
// Creates:
// 1. GDS projection: 'company-graph'
// 2. Node Similarity: GDS_SIMILAR relationships
// 3. PageRank: Company.pagerank property
// 4. Louvain Community Detection: Company.community property
// 5. FastRP Embeddings: Company.embedding property (128-dim)
//
// Prerequisites:
// - GDS plugin installed in Neo4j
// - Company nodes exist
// - CORRELATED_WITH relationships exist
// ============================================================================

// ----------------------------------------------------------------------------
// STEP 0: Verify Prerequisites
// ----------------------------------------------------------------------------

// Check Company nodes exist
MATCH (c:Company)
RETURN COUNT(c) AS company_count;

// Check CORRELATED_WITH relationships exist
MATCH ()-[r:CORRELATED_WITH]-()
RETURN COUNT(r) AS correlation_count;

// ----------------------------------------------------------------------------
// STEP 1: Verify GDS Installation
// ----------------------------------------------------------------------------

// Check GDS version
CALL gds.version();

// List available GDS procedures
CALL gds.list() YIELD name, description
WHERE name CONTAINS 'similarity' OR name CONTAINS 'pagerank' OR name CONTAINS 'community' OR name CONTAINS 'fastRP'
RETURN name, description
LIMIT 10;

// ----------------------------------------------------------------------------
// STEP 2: Create GDS Projection (Idempotent)
// ----------------------------------------------------------------------------

// Drop existing projection if it exists (safe to run multiple times)
CALL gds.graph.drop('company-graph', false) YIELD graphName;

// Create projection using Company nodes and CORRELATED_WITH relationships
// Uses correlation value as relationship weight
// NOTE: Empty nodeProperties config - GDS doesn't support String properties
CALL gds.graph.project(
    'company-graph',
    'Company',
    {
        CORRELATED_WITH: {
            type: 'CORRELATED_WITH',
            orientation: 'UNDIRECTED',
            properties: {
                correlation: {
                    property: 'correlation',
                    defaultValue: 0.0
                }
            }
        }
    },
    {}
)
YIELD graphName, nodeCount, relationshipCount, projectMillis
RETURN graphName, nodeCount, relationshipCount, projectMillis;

// ----------------------------------------------------------------------------
// STEP 3: Node Similarity (Idempotent)
// ----------------------------------------------------------------------------

// Run Node Similarity algorithm
// Computes similarity between Company nodes based on shared correlation patterns
// Creates GDS_SIMILAR relationships with similarity scores
CALL gds.nodeSimilarity.write(
    'company-graph',
    {
        writeRelationshipType: 'GDS_SIMILAR',
        writeProperty: 'score',
        similarityCutoff: 0.1,
        topK: 5
    }
)
YIELD nodesCompared, relationshipsWritten, writeMillis
RETURN nodesCompared, relationshipsWritten, writeMillis;

// ----------------------------------------------------------------------------
// STEP 4: PageRank Centrality (Idempotent)
// ----------------------------------------------------------------------------

// Run PageRank on Company graph
// Uses CORRELATED_WITH relationships with correlation as weight
// Stores PageRank score as Company.pagerank property
CALL gds.pageRank.write(
    'company-graph',
    {
        maxIterations: 20,
        dampingFactor: 0.85,
        relationshipWeightProperty: 'correlation',
        writeProperty: 'pagerank'
    }
)
YIELD nodePropertiesWritten, ranIterations, didConverge, writeMillis
RETURN nodePropertiesWritten, ranIterations, didConverge, writeMillis;

// ----------------------------------------------------------------------------
// STEP 5: Community Detection - Louvain (Idempotent)
// ----------------------------------------------------------------------------

// Run Louvain community detection
// Identifies communities of companies with similar correlation patterns
// Stores community ID as Company.community property
CALL gds.louvain.write(
    'company-graph',
    {
        writeProperty: 'community',
        relationshipWeightProperty: 'correlation'
    }
)
YIELD communityCount, ranLevels, modularity, writeMillis
RETURN communityCount, ranLevels, modularity, writeMillis;

// ----------------------------------------------------------------------------
// STEP 6: FastRP Embeddings (Idempotent, Optional)
// ----------------------------------------------------------------------------

// Create FastRP embeddings for Company nodes
// Embeddings capture structural similarity in the graph
// Can be used for semantic similarity search in GraphRAG
CALL gds.fastRP.write(
    'company-graph',
    {
        embeddingDimension: 128,
        iterationWeights: [0.0, 1.0, 1.0],
        relationshipWeightProperty: 'correlation',
        writeProperty: 'embedding'
    }
)
YIELD nodePropertiesWritten, writeMillis
RETURN nodePropertiesWritten, writeMillis;

// ----------------------------------------------------------------------------
// VERIFICATION QUERIES
// ----------------------------------------------------------------------------

// V1: Verify projection exists
CALL gds.graph.list() YIELD graphName, nodeCount, relationshipCount
WHERE graphName = 'company-graph'
RETURN graphName, nodeCount, relationshipCount;

// V2: Top similar companies for AAPL (Node Similarity)
MATCH (c1:Company {symbol: 'AAPL'})-[r:GDS_SIMILAR]-(c2:Company)
RETURN c2.symbol AS company, r.score AS similarity_score
ORDER BY r.score DESC
LIMIT 5;

// V3: Highest PageRank companies
MATCH (c:Company)
WHERE c.pagerank IS NOT NULL
RETURN c.symbol, c.pagerank
ORDER BY c.pagerank DESC
LIMIT 10;

// V4: Detected communities
MATCH (c:Company)
WHERE c.community IS NOT NULL
WITH c.community AS community, COLLECT(c.symbol) AS companies, COUNT(c) AS size
RETURN community, size, companies
ORDER BY size DESC;

// V5: Community distribution
MATCH (c:Company)
WHERE c.community IS NOT NULL
RETURN c.community AS community, COUNT(c) AS company_count
ORDER BY company_count DESC;

// V6: Companies with embeddings
MATCH (c:Company)
WHERE c.embedding IS NOT NULL
RETURN c.symbol, SIZE(c.embedding) AS embedding_dimension
LIMIT 5;

// V7: Sample embedding values (first 5 dimensions)
MATCH (c:Company {symbol: 'AAPL'})
WHERE c.embedding IS NOT NULL
RETURN c.symbol, c.embedding[0..5] AS embedding_sample;
