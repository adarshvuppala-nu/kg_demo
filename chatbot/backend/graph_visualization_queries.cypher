// ============================================================================
// GRAPH VISUALIZATION QUERIES FOR NEO4J BROWSER
// ============================================================================
// These queries are optimized for visualization in Neo4j Browser
// Run them to see beautiful graph visualizations of your data
// ============================================================================

// ----------------------------------------------------------------------------
// VISUALIZATION 1: Sector-Based Company Network
// ----------------------------------------------------------------------------
// Shows all companies connected to their sectors
// Great for seeing sector distribution
// ----------------------------------------------------------------------------

MATCH (c:Company)-[:IN_SECTOR]->(s:Sector)
RETURN c, s
LIMIT 50;

// ----------------------------------------------------------------------------
// VISUALIZATION 2: Technology Sector with GDS Similarity
// ----------------------------------------------------------------------------
// Shows Technology companies and how they move together (GDS_SIMILAR)
// Shows both sector relationships and similarity relationships
// ----------------------------------------------------------------------------

MATCH (c1:Company)-[:IN_SECTOR]->(s:Sector {name: 'Technology'})
MATCH (c2:Company)-[:IN_SECTOR]->(s)
MATCH (c1)-[r:GDS_SIMILAR]-(c2)
WHERE c1 <> c2 AND r.score > 0.5
RETURN c1, c2, s, r
LIMIT 30;

// ----------------------------------------------------------------------------
// VISUALIZATION 3: Cross-Sector Similarity Network
// ----------------------------------------------------------------------------
// Shows how companies in different sectors move together
// Visualizes cross-sector relationships
// ----------------------------------------------------------------------------

MATCH (c1:Company)-[:IN_SECTOR]->(s1:Sector)
MATCH (c2:Company)-[:IN_SECTOR]->(s2:Sector)
MATCH (c1)-[r:GDS_SIMILAR]-(c2)
WHERE c1 <> c2 AND s1 <> s2 AND r.score > 0.5
RETURN c1, c2, s1, s2, r
LIMIT 40;

// ----------------------------------------------------------------------------
// VISUALIZATION 4: Complete Company Network with All Relationships
// ----------------------------------------------------------------------------
// Shows companies with sectors, locations, and GDS similarities
// Most comprehensive view
// ----------------------------------------------------------------------------

MATCH (c:Company)
OPTIONAL MATCH (c)-[:IN_SECTOR]->(s:Sector)
OPTIONAL MATCH (c)-[:LOCATED_IN]->(co:Country)
OPTIONAL MATCH (c)-[r:GDS_SIMILAR]-(c2:Company)
WHERE r.score > 0.6
RETURN c, s, co, c2, r
LIMIT 50;

// ----------------------------------------------------------------------------
// VISUALIZATION 5: Sector Hierarchy with Company Counts
// ----------------------------------------------------------------------------
// Shows sectors and how many companies are in each
// Good for understanding sector distribution
// ----------------------------------------------------------------------------

MATCH (s:Sector)
OPTIONAL MATCH (c:Company)-[:IN_SECTOR]->(s)
WITH s, COUNT(c) AS company_count
WHERE company_count > 0
MATCH (c2:Company)-[:IN_SECTOR]->(s)
RETURN s, c2, company_count
ORDER BY company_count DESC
LIMIT 30;

// ----------------------------------------------------------------------------
// VISUALIZATION 6: Apple's Complete Network
// ----------------------------------------------------------------------------
// Shows everything connected to Apple:
// - Sector, Location, Similar companies, Stock prices
// ----------------------------------------------------------------------------

MATCH (apple:Company {symbol: 'AAPL'})
OPTIONAL MATCH (apple)-[:IN_SECTOR]->(s:Sector)
OPTIONAL MATCH (apple)-[:LOCATED_IN]->(co:Country)
OPTIONAL MATCH (apple)-[:IN_STATE]->(st:State)
OPTIONAL MATCH (apple)-[:IN_CITY]->(ci:City)
OPTIONAL MATCH (apple)-[r:GDS_SIMILAR]-(similar:Company)
WHERE r.score > 0.5
OPTIONAL MATCH (apple)-[:HAS_PRICE]->(p:PriceDay)
WHERE p.date >= date() - duration({days: 30})
RETURN apple, s, co, st, ci, similar, r, p
LIMIT 100;

// ----------------------------------------------------------------------------
// VISUALIZATION 7: Sector Communities (GDS Community Detection)
// ----------------------------------------------------------------------------
// Shows companies grouped by community and sector
// Visualizes market segments
// ----------------------------------------------------------------------------

MATCH (c1:Company)
WHERE c1.community IS NOT NULL
MATCH (c2:Company)
WHERE c2.community = c1.community AND c1 <> c2
OPTIONAL MATCH (c1)-[:IN_SECTOR]->(s1:Sector)
OPTIONAL MATCH (c2)-[:IN_SECTOR]->(s2:Sector)
RETURN c1, c2, s1, s2
LIMIT 50;

// ----------------------------------------------------------------------------
// VISUALIZATION 8: High Similarity Network (Top Connections)
// ----------------------------------------------------------------------------
// Shows only the strongest GDS similarity relationships
// Clean view of most correlated companies
// ----------------------------------------------------------------------------

MATCH (c1:Company)-[r:GDS_SIMILAR]-(c2:Company)
WHERE r.score > 0.7
OPTIONAL MATCH (c1)-[:IN_SECTOR]->(s1:Sector)
OPTIONAL MATCH (c2)-[:IN_SECTOR]->(s2:Sector)
RETURN c1, c2, s1, s2, r
ORDER BY r.score DESC
LIMIT 30;

// ----------------------------------------------------------------------------
// VISUALIZATION 9: Location-Based Network
// ----------------------------------------------------------------------------
// Shows companies by location (Country, State, City)
// Geographic distribution visualization
// ----------------------------------------------------------------------------

MATCH (c:Company)
OPTIONAL MATCH (c)-[:LOCATED_IN]->(co:Country)
OPTIONAL MATCH (c)-[:IN_STATE]->(st:State)
OPTIONAL MATCH (c)-[:IN_CITY]->(ci:City)
WHERE co IS NOT NULL
RETURN c, co, st, ci
LIMIT 50;

// ----------------------------------------------------------------------------
// VISUALIZATION 10: Multi-Layer Network (Sector + Similarity + Prices)
// ----------------------------------------------------------------------------
// Most complex visualization showing all relationship types
// Best for comprehensive understanding
// ----------------------------------------------------------------------------

MATCH (c:Company)-[:IN_SECTOR]->(s:Sector)
MATCH (c)-[r:GDS_SIMILAR]-(c2:Company)
WHERE r.score > 0.6
OPTIONAL MATCH (c)-[:HAS_PRICE]->(p:PriceDay)
WHERE p.date >= date() - duration({days: 7})
RETURN c, s, c2, r, p
LIMIT 40;

