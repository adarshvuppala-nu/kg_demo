// ============================================================================
// EXTENDED NEO4J SCHEMA FOR GRAPHRAG
// ============================================================================
// This script extends the base schema with time dimensions and derived
// relationships for complex reasoning and analytics.
//
// Base Schema:
//   (:Company {symbol}) -[:HAS_PRICE]-> (:PriceDay {date, open, high, low, close, adj_close, volume})
//
// Extended Schema:
//   - Time dimension nodes (Year, Quarter, Month)
//   - Derived relationships (CORRELATED_WITH, OUTPERFORMED)
//   - Aggregated metrics for performance analysis
// ============================================================================

// ----------------------------------------------------------------------------
// STEP 1: Create Time Dimension Nodes
// ----------------------------------------------------------------------------

// Create Year nodes
MATCH (p:PriceDay)
WITH DISTINCT date(p.date).year AS year
MERGE (y:Year {year: year})
RETURN COUNT(y) AS years_created;

// Create Quarter nodes
MATCH (p:PriceDay)
WITH DISTINCT date(p.date).year AS year, date(p.date).quarter AS quarter
MERGE (q:Quarter {year: year, quarter: quarter})
RETURN COUNT(q) AS quarters_created;

// Create Month nodes
MATCH (p:PriceDay)
WITH DISTINCT date(p.date).year AS year, date(p.date).month AS month
MERGE (m:Month {year: year, month: month})
RETURN COUNT(m) AS months_created;

// ----------------------------------------------------------------------------
// STEP 2: Link PriceDay nodes to Time Dimensions
// ----------------------------------------------------------------------------

// Link PriceDay to Year
MATCH (p:PriceDay), (y:Year {year: date(p.date).year})
MERGE (p)-[:IN_YEAR]->(y);

// Link PriceDay to Quarter
MATCH (p:PriceDay), (q:Quarter {year: date(p.date).year, quarter: date(p.date).quarter})
MERGE (p)-[:IN_QUARTER]->(q);

// Link PriceDay to Month
MATCH (p:PriceDay), (m:Month {year: date(p.date).year, month: date(p.date).month})
MERGE (p)-[:IN_MONTH]->(m);

// ----------------------------------------------------------------------------
// STEP 3: Create Aggregated Metrics (Yearly Performance)
// ----------------------------------------------------------------------------

// Calculate yearly performance for each company
MATCH (c:Company)-[:HAS_PRICE]->(p:PriceDay)-[:IN_YEAR]->(y:Year)
WITH c, y, 
     MIN(p.date) AS first_date,
     MAX(p.date) AS last_date,
     COLLECT(p) AS prices
WITH c, y, first_date, last_date, prices,
     [p IN prices WHERE p.date = first_date][0] AS first_price,
     [p IN prices WHERE p.date = last_date][0] AS last_price
WHERE first_price IS NOT NULL AND last_price IS NOT NULL
WITH c, y, 
     first_price.close AS start_price,
     last_price.close AS end_price,
     ((last_price.close - first_price.close) / first_price.close * 100) AS return_pct
MERGE (c)-[r:PERFORMED_IN {year: y.year, return_pct: return_pct, start_price: start_price, end_price: end_price}]->(y)
RETURN COUNT(r) AS yearly_performance_rels;

// ----------------------------------------------------------------------------
// STEP 4: Create Correlation Relationships (based on price movements)
// ----------------------------------------------------------------------------

// Calculate correlation between companies based on daily returns
// This uses a simplified correlation: compare daily return patterns
MATCH (c1:Company)-[:HAS_PRICE]->(p1:PriceDay)
MATCH (c2:Company)-[:HAS_PRICE]->(p2:PriceDay)
WHERE c1.symbol < c2.symbol  // Avoid duplicates
  AND p1.date = p2.date
WITH c1, c2, 
     COLLECT({
       date: p1.date,
       return1: (p1.close - p1.open) / p1.open,
       return2: (p2.close - p2.open) / p2.open
     }) AS daily_returns
WHERE SIZE(daily_returns) >= 30  // Minimum 30 days for correlation
WITH c1, c2, daily_returns,
     REDUCE(s1 = 0.0, r IN daily_returns | s1 + r.return1) / SIZE(daily_returns) AS mean1,
     REDUCE(s2 = 0.0, r IN daily_returns | s2 + r.return2) / SIZE(daily_returns) AS mean2
WITH c1, c2, daily_returns, mean1, mean2,
     REDUCE(numerator = 0.0, r IN daily_returns | 
       numerator + (r.return1 - mean1) * (r.return2 - mean2)
     ) AS numerator,
     SQRT(REDUCE(sum1 = 0.0, r IN daily_returns | sum1 + (r.return1 - mean1)^2)) AS std1,
     SQRT(REDUCE(sum2 = 0.0, r IN daily_returns | sum2 + (r.return2 - mean2)^2)) AS std2
WHERE std1 > 0 AND std2 > 0
WITH c1, c2, (numerator / (std1 * std2)) AS correlation
WHERE ABS(correlation) >= 0.3  // Only store meaningful correlations
MERGE (c1)-[r:CORRELATED_WITH {correlation: correlation, sample_size: SIZE(daily_returns)}]-(c2)
RETURN COUNT(r) AS correlation_rels;

// ----------------------------------------------------------------------------
// STEP 5: Create Indexes for Performance
// ----------------------------------------------------------------------------

CREATE INDEX year_index IF NOT EXISTS FOR (y:Year) ON (y.year);
CREATE INDEX quarter_index IF NOT EXISTS FOR (q:Quarter) ON (q.year, q.quarter);
CREATE INDEX month_index IF NOT EXISTS FOR (m:Month) ON (m.year, m.month);
CREATE INDEX priceday_date_index IF NOT EXISTS FOR (p:PriceDay) ON (p.date);
CREATE INDEX priceday_symbol_index IF NOT EXISTS FOR (p:PriceDay) ON (p.symbol);

// ----------------------------------------------------------------------------
// STEP 6: Verify Schema
// ----------------------------------------------------------------------------

// Count nodes by type
MATCH (n)
RETURN labels(n)[0] AS node_type, COUNT(n) AS count
ORDER BY count DESC;

// Count relationships by type
MATCH ()-[r]->()
RETURN type(r) AS rel_type, COUNT(r) AS count
ORDER BY count DESC;

