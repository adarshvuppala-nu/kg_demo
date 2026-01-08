# Extended Graph Schema for GraphRAG with Schema Safety
# Based on langchain-neo4j pattern: strict schema enforcement
from typing import Tuple, Optional

# Complete schema definition (EXACT - no variations allowed)
EXTENDED_GRAPH_SCHEMA = """Neo4j Graph Schema (STRICT - use ONLY these):

NODE TYPES:
1. Company {symbol: String, sector: String, fulltimeemployees: Integer, marketcap: Float}
2. PriceDay {date: Date, open: Float, high: Float, low: Float, close: Float, adj_close: Float, volume: Integer}
3. Year {year: Integer}
4. Quarter {year: Integer, quarter: Integer}
5. Month {year: Integer, month: Integer}
6. Sector {name: String}
7. Country {name: String}
8. State {name: String, country: String}
9. City {name: String, state: String, country: String}

RELATIONSHIP TYPES (EXACT):
1. (:Company)-[:HAS_PRICE]->(:PriceDay)
2. (:PriceDay)-[:IN_YEAR]->(:Year)
3. (:PriceDay)-[:IN_QUARTER]->(:Quarter)
4. (:PriceDay)-[:IN_MONTH]->(:Month)
5. (:Company)-[:PERFORMED_IN {return_pct: Float, start_price: Float, end_price: Float}]->(:Year)
6. (:Company)-[:CORRELATED_WITH {correlation: Float, sample_size: Integer}]-(:Company)
7. (:Company)-[:GDS_SIMILAR {score: Float}]-(:Company)  // GDS Node Similarity
8. (:Company)-[:IN_SECTOR]->(:Sector)
9. (:Company)-[:LOCATED_IN]->(:Country)
10. (:Company)-[:IN_STATE]->(:State)
11. (:Company)-[:IN_CITY]->(:City)
12. (:State)-[:IN_COUNTRY]->(:Country)
13. (:City)-[:IN_STATE]->(:State)

SCHEMA RULES (MANDATORY):
- ONLY use the 9 node types listed above
- ONLY use the 13 relationship types listed above (includes GDS_SIMILAR)
- NEVER invent new node labels or relationship types
- ALWAYS use parameters: $symbol, $year, $date, etc.
- Date format: Use date() function or date literals like date('2022-01-01')
- Year property: Use date(p.date).year or y.year
- Quarter property: Use date(p.date).quarter or q.quarter
- Month property: Use date(p.date).month or m.month

VALID QUERY PATTERNS:

1. Latest price:
MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay)
RETURN p.date, p.close, p.volume
ORDER BY p.date DESC LIMIT 1

2. Price in year:
MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay)-[:IN_YEAR]->(y:Year {year: $year})
RETURN p.date, p.close ORDER BY p.date

3. Yearly performance:
MATCH (c:Company {symbol: $symbol})-[:PERFORMED_IN]->(y:Year {year: $year})
RETURN y.year, c.return_pct, c.start_price, c.end_price

4. Correlation:
MATCH (c1:Company {symbol: $symbol1})-[r:CORRELATED_WITH]-(c2:Company)
RETURN c2.symbol, r.correlation ORDER BY ABS(r.correlation) DESC LIMIT 5

5. Trend (quarterly):
MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay)-[:IN_QUARTER]->(q:Quarter {year: $year})
WITH q, AVG(p.close) AS avg_price
RETURN q.quarter, avg_price ORDER BY q.quarter

6. Comparison:
MATCH (c1:Company {symbol: $symbol1})-[:PERFORMED_IN]->(y:Year {year: $year})
MATCH (c2:Company {symbol: $symbol2})-[:PERFORMED_IN]->(y)
RETURN c1.symbol, c1.return_pct, c2.symbol, c2.return_pct

7. Sector query:
MATCH (c:Company)-[:IN_SECTOR]->(s:Sector {name: $sector})
RETURN c.symbol, c.sector ORDER BY c.symbol

8. Companies in same sector:
MATCH (c1:Company {symbol: $symbol})-[:IN_SECTOR]->(s:Sector)
MATCH (c2:Company)-[:IN_SECTOR]->(s)
WHERE c1 <> c2
RETURN c2.symbol, c2.sector

9. Sector-based similarity:
MATCH (c1:Company {symbol: $symbol})-[:IN_SECTOR]->(s:Sector)
MATCH (c2:Company)-[:IN_SECTOR]->(s)
MATCH (c1)-[r:GDS_SIMILAR]-(c2)
WHERE c1 <> c2
RETURN c2.symbol, r.score, c2.sector
ORDER BY r.score DESC LIMIT 5

10. Company sector:
MATCH (c:Company {symbol: $symbol})-[:IN_SECTOR]->(s:Sector)
RETURN c.symbol, s.name AS sector

INVALID (DO NOT USE):
- Any node label not in the 5 types above
- Any relationship type not in the 6 types above
- Creating new nodes (CREATE, MERGE with new labels)
- Properties not defined in schema
- Direct date comparisons without time dimensions
"""

# Legacy schema (kept for backward compatibility)
GRAPH_SCHEMA = """Neo4j Schema:
Company {symbol} -[:HAS_PRICE]-> PriceDay {date, close, volume, open, high, low}

Extended Schema (for advanced queries):
- Time dimensions: Year {year}, Quarter {year, quarter}, Month {year, month}
- Relationships: 
  - (:PriceDay)-[:IN_YEAR]->(:Year)
  - (:Company)-[:PERFORMED_IN {return_pct, start_price, end_price}]->(:Year)
  - (:Company)-[:CORRELATED_WITH {correlation, sample_size}]-(:Company)

Examples:
- Latest: MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay) RETURN p.date, p.close, p.volume ORDER BY p.date DESC LIMIT 1
- List: MATCH (c:Company) RETURN c.symbol LIMIT 10
- Performance: MATCH (c:Company {symbol: $symbol})-[:PERFORMED_IN]->(y:Year {year: $year}) RETURN y.year, c.return_pct
- Correlation: MATCH (c1:Company {symbol: $symbol1})-[r:CORRELATED_WITH]-(c2:Company) RETURN c2.symbol, r.correlation ORDER BY ABS(r.correlation) DESC LIMIT 5"""

def get_cypher_generation_prompt(question: str, use_extended: bool = True, context: Optional[dict] = None) -> str:
    """
    Generate a schema-safe prompt for LLM to create Cypher query.
    Inspired by langchain-neo4j pattern with strict schema enforcement.
    
    Args:
        question: User's natural language question
        use_extended: Whether to use extended schema (default: True)
    
    Returns:
        Prompt string for LLM
    """
    # Use extended schema for complex queries
    question_lower = question.lower()
    is_complex = any(word in question_lower for word in [
        "outperform", "compare", "trend", "correlat", "similar", "influential",
        "pagerank", "community", "group", "vs", "versus", "better", "worse",
        "moves with", "moves together", "move with", "similar stocks", "similar companies",
        "same group", "market segment", "important", "central",
        "sector", "industry", "belong to", "same sector", "which sector", "what sector"
    ])
    
    schema = EXTENDED_GRAPH_SCHEMA if (use_extended or is_complex) else GRAPH_SCHEMA
    
    # Few-shot examples for common query patterns
    few_shot_examples = """
FEW-SHOT EXAMPLES:

Example 1 - Latest Price:
Question: "What is the latest price of MSFT?"
Query: MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay)
      RETURN p.date, p.close, p.volume
      ORDER BY p.date DESC
      LIMIT 1

Example 2 - Price History:
Question: "Show me AAPL prices in 2022"
Query: MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay)
      WHERE p.date >= date('2022-01-01') AND p.date <= date('2022-12-31')
      RETURN p.date, p.close
      ORDER BY p.date

Example 3 - Company List:
Question: "What companies are available?"
Query: MATCH (c:Company)
      RETURN c.symbol
      LIMIT 10

Example 4 - Volume Query:
Question: "What is the trading volume of TSLA?"
Query: MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay)
      RETURN p.date, p.volume
      ORDER BY p.date DESC
      LIMIT 1

Example 5 - Performance Comparison (Multi-hop):
Question: "Which stock outperformed AAPL in 2022?"
Query: MATCH (c1:Company {symbol: "AAPL"})-[:PERFORMED_IN]->(y:Year {year: 2022})
      MATCH (c2:Company)-[r2:PERFORMED_IN]->(y)
      WHERE c2.symbol <> c1.symbol AND r2.return_pct > c1.return_pct
      RETURN c2.symbol, r2.return_pct AS return_pct
      ORDER BY r2.return_pct DESC
      LIMIT 5

Example 6 - Correlation Query (CORRELATED_WITH):
Question: "Which stocks are most correlated with TSLA?" OR "What stocks move with TSLA?"
Query: MATCH (c1:Company {symbol: $symbol})-[r:CORRELATED_WITH]-(c2:Company)
      RETURN c2.symbol, r.correlation
      ORDER BY ABS(r.correlation) DESC
      LIMIT 5

Example 6b - Stocks That Move Together (GDS Similarity):
Question: "Which stocks moves with MSFT?" OR "What stocks move together with Microsoft?" OR "Which stocks moves with Apple?"
Query: MATCH (c1:Company {symbol: $symbol})-[r:GDS_SIMILAR]-(c2:Company)
      RETURN c2.symbol AS similar_stock, r.score AS similarity_score
      ORDER BY r.score DESC
      LIMIT 5

Example 7 - Sector Query:
Question: "What sector does Apple belong to?" OR "Which sector is AAPL in?"
Query: MATCH (c:Company {symbol: $symbol})-[:IN_SECTOR]->(s:Sector)
      RETURN c.symbol, s.name AS sector

Example 8 - Companies in Same Sector:
Question: "What other companies are in the same sector as Apple?" OR "Which companies are in Technology sector?"
Query: MATCH (c1:Company {symbol: $symbol})-[:IN_SECTOR]->(s:Sector)
      MATCH (c2:Company)-[:IN_SECTOR]->(s)
      WHERE c1 <> c2
      RETURN c2.symbol, s.name AS sector
      ORDER BY c2.symbol
      LIMIT 10

Example 9 - Sector-Based Similarity:
Question: "Which companies in the same sector as Apple move together?" OR "What Technology companies move with Apple?"
Query: MATCH (c1:Company {symbol: $symbol})-[:IN_SECTOR]->(s:Sector)
      MATCH (c2:Company)-[:IN_SECTOR]->(s)
      MATCH (c1)-[r:GDS_SIMILAR]-(c2)
      WHERE c1 <> c2
      RETURN c2.symbol, r.score AS similarity_score, s.name AS sector
      ORDER BY r.score DESC
      LIMIT 5

Example 10 - GDS Similarity Query:
Question: "Which companies are similar to AAPL?" OR "Find similar stocks to Apple" OR "Which stocks are similar to Microsoft?"
Query: MATCH (c1:Company {symbol: $symbol})-[r:GDS_SIMILAR]-(c2:Company)
      RETURN c2.symbol AS similar_stock, r.score AS similarity_score
      ORDER BY r.score DESC
      LIMIT 5

Example 11 - PageRank Query:
Question: "What are the most influential companies?" OR "Top 3 companies by PageRank" OR "Most important stocks"
Query: MATCH (c:Company)
      WHERE c.pagerank IS NOT NULL
      RETURN c.symbol, c.pagerank
      ORDER BY c.pagerank DESC
      LIMIT 3

Example 12 - Community Query:
Question: "What companies are in the same group as MSFT?" OR "Which stocks are in MSFT's market segment?"
Query: MATCH (c1:Company {symbol: $symbol})
      WHERE c1.community IS NOT NULL
      MATCH (c2:Company)
      WHERE c2.community = c1.community AND c2.symbol <> c1.symbol
      RETURN c2.symbol

Example 7 - Temporal Trend (Multi-hop with time dimensions):
Question: "Show me AAPL price trend over the last 5 years" OR "NVDA price trend over last 5 years"
Query: MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay)-[:IN_YEAR]->(y:Year)
      WHERE y.year >= date().year - 5
      WITH y.year AS year, AVG(p.close) AS avg_price, MIN(p.close) AS min_price, MAX(p.close) AS max_price
      RETURN year, avg_price, min_price, max_price
      ORDER BY year

Example 8 - Multi-company Comparison (Complex multi-hop):
Question: "Compare AAPL and MSFT performance in 2023"
Query: MATCH (c1:Company {symbol: "AAPL"})-[:PERFORMED_IN]->(y:Year {year: 2023})
      MATCH (c2:Company {symbol: "MSFT"})-[:PERFORMED_IN]->(y)
      RETURN c1.symbol, c1.return_pct AS aapl_return, c2.symbol, c2.return_pct AS msft_return

Example 9 - Year-over-Year Growth (Temporal reasoning):
Question: "How did NVDA perform in 2022 vs 2023?"
Query: MATCH (c:Company {symbol: $symbol})-[:PERFORMED_IN]->(y:Year)
      WHERE y.year IN [2022, 2023]
      RETURN y.year, c.return_pct
      ORDER BY y.year
"""
    
    # Build intelligent context from conversation history
    context_hint = ""
    if context:
        # Add recent conversation history
        if context.get('message_history'):
            recent = context.get('message_history', [])[-3:]  # Last 3 messages
            if recent:
                context_hint = "\n\nCONVERSATION CONTEXT:\n"
                for msg in recent:
                    q = msg.get('question', msg.get('content', ''))
                    a = msg.get('answer', '')
                    if q:
                        context_hint += f"User asked: {q}\n"
                    if a:
                        context_hint += f"Bot answered: {a[:80]}...\n"
        
        # Add recently discussed symbols
        if context.get('recent_symbols'):
            context_hint += f"\nRecently discussed companies: {', '.join(context.get('recent_symbols', []))}"
        
        # Add last symbol for follow-ups
        if context.get('last_symbol'):
            context_hint += f"\nLast symbol mentioned: {context.get('last_symbol')}"
        
        # Add recent topics
        if context.get('recent_topics'):
            context_hint += f"\nRecent conversation topics: {', '.join(context.get('recent_topics', []))}"
    
    return f"""You are an intelligent Cypher query generator for a Neo4j stock price knowledge graph.
You understand conversation context and can generate appropriate queries based on what was discussed before.

{schema}

{few_shot_examples}

User Question: {question}
{context_hint}

CRITICAL RULES:
1. Return ONLY a valid Cypher query, no explanations, no markdown code blocks, no backticks
2. Use ONLY the node types and relationships defined in the schema above
3. For multi-hop queries, use multiple MATCH clauses connected by relationships
4. For temporal queries, use time dimension nodes (Year, Quarter, Month) via IN_YEAR, IN_QUARTER, IN_MONTH
5. For comparisons, use PERFORMED_IN relationships to Year nodes
6. For correlations or "moves with" questions, use CORRELATED_WITH relationships between Company nodes
7. For similarity or "similar stocks" questions, use GDS_SIMILAR relationships (NOT CORRELATED_WITH)
8. For "moves with", "moves together", "similar stocks" questions, prefer GDS_SIMILAR over CORRELATED_WITH
9. For PageRank questions ("influential", "important", "central"), use Company.pagerank property
10. For community/group questions, use Company.community property
11. For sector questions ("what sector", "which sector", "same sector"), use IN_SECTOR relationship
12. For companies in same sector, match both companies to the same Sector node
13. For sector-based similarity, combine IN_SECTOR with GDS_SIMILAR relationships
14. ALWAYS use $symbol parameter (do NOT hardcode symbol values unless absolutely necessary)
15. If the question cannot be answered with the schema, return: "INVALID_QUESTION"
16. Follow the examples above for query structure
14. For trends over time, use aggregation functions (AVG, MIN, MAX) with GROUP BY

Generate the Cypher query now:"""

def get_qa_prompt(question: str, data: list, query_type: str = "general", context: Optional[dict] = None) -> str:
    """
    Generate a prompt for LLM to convert query results into natural language.
    Enhanced for different query types (trends, comparisons, correlations).
    Now includes conversation context for better understanding.
    
    Args:
        question: Original user question
        data: Query results (list of dicts)
        query_type: Type of query (general, trend, comparison, correlation)
        context: Optional conversation context
    
    Returns:
        Prompt string for LLM
    """
    # Build context hint if available
    context_hint = ""
    if context:
        if context.get('last_question'):
            context_hint += f"\nPrevious question: {context.get('last_question')}"
        if context.get('last_answer'):
            context_hint += f"\nPrevious answer summary: {context.get('last_answer')[:100]}..."
        if context.get('extracted_symbol'):
            context_hint += f"\nCompany mentioned: {context.get('extracted_symbol')}"
    
    base_prompt = f"""You are a helpful, intelligent, and conversational financial assistant chatbot. Answer the user's question using ONLY the provided data from Neo4j GraphRAG.

CRITICAL: You MUST use ONLY the data provided below. Do NOT use external knowledge or make up numbers.

User Question: {question}
{context_hint}

Data from Neo4j GraphRAG query (this is the ONLY data you can use):
{data}

Instructions:
- Be conversational, friendly, and helpful (like ChatGPT) BUT use ONLY the provided data
- If data is missing or shows None, explain what that means based on the data structure
- If the question asks "what factors" or "how", explain based on what the data shows
- If data shows None values, explain that the data is not available in the database
- Reference previous conversation naturally when relevant
- Format numbers clearly (prices with $, percentages with %)
- Be concise but informative
- DO NOT invent or estimate numbers - use only what's in the data
- If data is empty or all None, explain that clearly

Answer:"""
    
    if query_type == "trend":
        return f"""{base_prompt}
- Describe the price trend over time
- Highlight significant changes or patterns
- Use specific dates and prices from the data
- Be concise and factual"""
    
    elif query_type == "comparison":
        return f"""{base_prompt}
- Compare the performance between companies or time periods
- Highlight which performed better and by how much (use percentages, prices, returns)
- Calculate differences when comparing two items
- Use specific numbers from the data
- Be clear and objective
- If comparing years, mention the year-over-year change"""
    
    elif query_type == "correlation":
        return f"""{base_prompt}
- Explain the correlation between stocks
- Interpret correlation values (positive/negative, strength)
- Mention which stocks are most/least correlated
- Use correlation values from the data
- Explain what correlation means (how stocks move together)"""
    
    elif query_type == "similarity" or "GDS_SIMILAR" in str(data).upper():
        return f"""{base_prompt}
- Explain which companies are similar and why
- Mention similarity scores (higher = more similar)
- Suggest why they might be similar (sector, correlation patterns)
- Be concise and factual"""
    
    elif query_type == "centrality" or "pagerank" in str(data).upper():
        return f"""{base_prompt}
- Explain PageRank scores (higher = more influential)
- Rank companies by importance
- Explain what makes a company central in the network
- Use specific PageRank values from the data"""
    
    elif query_type == "community":
        return f"""{base_prompt}
- Explain which companies are in the same community
- Group companies by market segments
- Explain why companies are grouped together
- Use community information from the data"""
    
    else:
        return f"""{base_prompt}
- Answer like ChatGPT - naturally, intelligently, and conversationally BUT use ONLY the provided data
- If data is missing or shows None, explain that the data is not available in the database
- If the question asks "what factors" or "how", explain based on what the data structure shows
- If data is empty or all None, explain clearly that the data is not available
- Include specific numbers from data when available (prices with $, dates as YYYY-MM-DD)
- Reference previous conversation naturally
- Be helpful and informative - explain what the data shows, even if it's None
- DO NOT make up numbers or use external knowledge
- Format everything clearly and professionally
- If return_pct is None, explain that performance data is not available in the database

Answer (be intelligent, conversational, and helpful, but use ONLY the provided data):"""

def validate_cypher_query(query: str) -> Tuple[bool, str]:
    """
    Validate that a Cypher query only uses allowed schema elements.
    Returns (is_valid, error_message)
    """
    query_upper = query.upper()
    
    # Allowed node labels
    allowed_nodes = ["COMPANY", "PRICEDAY", "YEAR", "QUARTER", "MONTH", "SECTOR", "COUNTRY", "STATE", "CITY"]
    
    # Allowed relationships
    allowed_rels = ["HAS_PRICE", "IN_YEAR", "IN_QUARTER", "IN_MONTH", 
                    "PERFORMED_IN", "CORRELATED_WITH", "GDS_SIMILAR",
                    "IN_SECTOR", "LOCATED_IN", "IN_STATE", "IN_CITY", "IN_COUNTRY"]
    
    # Check for forbidden operations
    forbidden_ops = ["CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DETACH DELETE"]
    for op in forbidden_ops:
        if op in query_upper:
            return False, f"Query contains forbidden operation: {op}. Only SELECT queries allowed."
    
    # Check for common invalid patterns
    invalid_patterns = [
        ("NODE", "Use specific node labels: Company, PriceDay, Year, Quarter, Month"),
        ("RELATIONSHIP", "Use specific relationship types from schema"),
    ]
    
    # Extract node labels from query (pattern: :Label or (n:Label))
    import re
    # Match node labels: (n:Label) or :Label in MATCH patterns
    node_patterns = [
        r'\([^)]*:(\w+)',  # (n:Label) or (:Label)
        r'\b:(\w+)\s*\('   # :Label before opening paren
    ]
    node_matches = []
    for pattern in node_patterns:
        node_matches.extend(re.findall(pattern, query))
    # Remove duplicates and check
    seen_nodes = set()
    for match in node_matches:
        match_upper = match.upper()
        if match_upper not in seen_nodes:
            seen_nodes.add(match_upper)
            if match_upper not in [n.upper() for n in allowed_nodes]:
                return False, f"Invalid node label '{match}'. Allowed: {', '.join(allowed_nodes)}"
    
    # Extract relationship types (pattern: [:REL_TYPE] or -[:REL_TYPE]-)
    rel_patterns = [
        r'\[:(\w+)',      # [:REL_TYPE]
        r'-\[:(\w+)\]',   # -[:REL_TYPE]-
        r'\[r:(\w+)'      # [r:REL_TYPE]
    ]
    rel_matches = []
    for pattern in rel_patterns:
        rel_matches.extend(re.findall(pattern, query))
    # Remove duplicates and check
    seen_rels = set()
    for match in rel_matches:
        match_upper = match.upper()
        if match_upper not in seen_rels:
            seen_rels.add(match_upper)
            if match_upper not in [r.upper() for r in allowed_rels]:
                return False, f"Invalid relationship type '{match}'. Allowed: {', '.join(allowed_rels)}"
    
    return True, ""

def detect_query_type(question: str, query: str) -> str:
    """
    Detect the type of query for appropriate QA prompt selection.
    Returns: "trend", "comparison", "correlation", "similarity", "centrality", "community", or "general"
    """
    question_lower = question.lower()
    query_upper = query.upper() if query else ""
    
    # GDS query types (check first)
    if "GDS_SIMILAR" in query_upper or any(word in question_lower for word in ["similar to", "similar companies", "similar stocks"]):
        return "similarity"
    
    if "PAGERANK" in query_upper or any(word in question_lower for word in ["influential", "pagerank", "central", "importance", "top companies by"]):
        return "centrality"
    
    if "COMMUNITY" in query_upper or any(word in question_lower for word in ["same group", "same community", "same segment", "in the same"]):
        return "community"
    
    # Trend indicators
    if any(word in question_lower for word in ["trend", "over time", "historical", "chart", "graph", "growth", "change over", "evolution", "last 5 years", "last 3 years"]):
        return "trend"
    
    # Comparison indicators
    if any(word in question_lower for word in ["compare", "vs", "versus", "better", "outperform", "difference", "worse", "beaten"]):
        return "comparison"
    
    # Correlation indicators (but prefer GDS_SIMILAR for "moves with")
    if any(word in question_lower for word in ["correlat", "relationship between", "most correlated"]):
        return "correlation"
    
    # GDS Similarity indicators (for "moves with", "similar stocks")
    if any(word in question_lower for word in ["moves with", "moves together", "move with", "similar stocks", "similar companies"]):
        return "similarity"
    
    # Check query structure
    if "CORRELATED_WITH" in query_upper:
        return "correlation"
    if "GDS_SIMILAR" in query_upper:
        return "similarity"
    if "PAGERANK" in query_upper:
        return "centrality"
    if "COMMUNITY" in query_upper:
        return "community"
    if "PERFORMED_IN" in query_upper and "MATCH" in query_upper and query_upper.count("MATCH") > 1:
        return "comparison"
    if "IN_QUARTER" in query_upper or "IN_MONTH" in query_upper or "IN_YEAR" in query_upper:
        if "AVG" in query_upper or "GROUP BY" in query_upper:
            return "trend"
    
    return "general"

# Legacy function (kept for backward compatibility)
def company_latest_price(symbol):
    """
    Legacy function - kept for backward compatibility.
    Use LLM-generated queries instead.
    """
    return """
    MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay)
    RETURN p.date, p.close, p.volume
    ORDER BY p.date DESC
    LIMIT 1
    """
