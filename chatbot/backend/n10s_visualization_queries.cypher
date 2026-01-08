// ============================================================================
// N10S ONTOLOGY VISUALIZATION QUERIES
// ============================================================================
// These queries show how n10s maps your Neo4j data to RDF/OWL ontology
// Run these in Neo4j Browser for visualization
// ============================================================================

// ----------------------------------------------------------------------------
// QUERY 1: Show Ontology Class Structure
// ----------------------------------------------------------------------------
// Visualizes the ontology classes and their relationships
// Shows: Company, PriceDay, Year, Quarter, Month and how they connect
// ----------------------------------------------------------------------------

MATCH (c:Company)-[:HAS_PRICE]->(p:PriceDay)-[:IN_YEAR]->(y:Year)
MATCH (p)-[:IN_QUARTER]->(q:Quarter)
MATCH (p)-[:IN_MONTH]->(m:Month)
RETURN c, p, y, q, m
LIMIT 50;

// ----------------------------------------------------------------------------
// QUERY 2: Show Companies with Their Ontology Mappings
// ----------------------------------------------------------------------------
// Visualizes Company nodes and their RDF class mappings
// Shows all companies with their properties
// ----------------------------------------------------------------------------

MATCH (c:Company)
OPTIONAL MATCH (c)-[:HAS_PRICE]->(p:PriceDay)
WITH c, collect(p)[0..5] as prices
RETURN c, prices
ORDER BY c.symbol
LIMIT 10;

// ----------------------------------------------------------------------------
// QUERY 3: Show Ontology Relationships (RDF Object Properties)
// ----------------------------------------------------------------------------
// Visualizes how ontology properties connect nodes
// Shows: hasPrice, correlatedWith, performedIn relationships
// ----------------------------------------------------------------------------

MATCH (c1:Company)-[r1:HAS_PRICE]->(p:PriceDay)
MATCH (c1)-[r2:CORRELATED_WITH]-(c2:Company)
MATCH (c1)-[r3:PERFORMED_IN]->(y:Year)
RETURN c1, c2, p, y, r1, r2, r3
LIMIT 30;

// ----------------------------------------------------------------------------
// QUERY 4: Show Complete Ontology Graph for One Company
// ----------------------------------------------------------------------------
// Visualizes the complete ontology structure for a single company
// Shows: Company → PriceDays → Time Dimensions → Performance
// ----------------------------------------------------------------------------

MATCH (c:Company {symbol: 'AAPL'})
OPTIONAL MATCH (c)-[:HAS_PRICE]->(p:PriceDay)-[:IN_YEAR]->(y:Year)
OPTIONAL MATCH (p)-[:IN_QUARTER]->(q:Quarter)
OPTIONAL MATCH (p)-[:IN_MONTH]->(m:Month)
OPTIONAL MATCH (c)-[:PERFORMED_IN]->(y2:Year)
OPTIONAL MATCH (c)-[:CORRELATED_WITH]-(c2:Company)
RETURN c, p, y, q, m, y2, c2
LIMIT 100;

// ----------------------------------------------------------------------------
// BONUS QUERY: Show n10s Mappings (Metadata)
// ----------------------------------------------------------------------------
// Shows the actual RDF mappings configured in n10s
// This is metadata about the ontology, not the data itself
// ----------------------------------------------------------------------------

// Note: This requires calling n10s.mapping.list() procedure
// For visualization, you can see mappings via:
CALL n10s.mapping.list() YIELD schemaElement, elemName
RETURN schemaElement AS rdf_class, elemName AS neo4j_label;

