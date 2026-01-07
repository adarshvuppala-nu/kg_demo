# Using GDS Outputs in GraphRAG

This document explains how the Graph Data Science (GDS) outputs can be used to enhance GraphRAG queries and responses.

## GDS Outputs Available

After running `gds_setup.py`, the following analytics are available:

1. **Node Similarity** (`GDS_SIMILAR` relationships)
2. **PageRank** (`Company.pagerank` property)
3. **Community Detection** (`Company.community` property)
4. **FastRP Embeddings** (`Company.embedding` property)

---

## 1. Node Similarity (`GDS_SIMILAR`)

### What It Is
Measures structural similarity between companies based on their correlation patterns in the graph.

### GraphRAG Usage

**Query Pattern:**
```cypher
// Find companies similar to a given company
MATCH (c1:Company {symbol: $symbol})-[r:GDS_SIMILAR]-(c2:Company)
RETURN c2.symbol, r.score
ORDER BY r.score DESC
LIMIT 5
```

**Example Questions:**
- "Which companies are most similar to AAPL?"
- "Find stocks that behave like TSLA"
- "What companies have similar trading patterns to MSFT?"

**GraphRAG Enhancement:**
- Use similarity scores to recommend related companies
- Explain why companies are similar (based on correlation patterns)
- Suggest comparisons between similar companies

---

## 2. PageRank Centrality (`Company.pagerank`)

### What It Is
Measures the importance/influence of each company in the correlation network. Higher PageRank = more central/important.

### GraphRAG Usage

**Query Pattern:**
```cypher
// Find most influential companies
MATCH (c:Company)
WHERE c.pagerank IS NOT NULL
RETURN c.symbol, c.pagerank
ORDER BY c.pagerank DESC
LIMIT 10
```

**Example Questions:**
- "Which companies are most influential in the market?"
- "What are the top central stocks?"
- "Show me the most important companies by network centrality"

**GraphRAG Enhancement:**
- Rank companies by importance, not just price
- Explain market influence and centrality
- Identify key players in the correlation network

---

## 3. Community Detection (`Company.community`)

### What It Is
Groups companies into communities based on correlation patterns. Companies in the same community tend to move together.

### GraphRAG Usage

**Query Pattern:**
```cypher
// Find companies in the same community
MATCH (c1:Company {symbol: $symbol})
WHERE c1.community IS NOT NULL
MATCH (c2:Company)
WHERE c2.community = c1.community AND c2.symbol <> c1.symbol
RETURN c2.symbol
ORDER BY c2.symbol
```

**Example Questions:**
- "What companies are in the same market segment as AAPL?"
- "Which stocks move together with MSFT?"
- "Show me all companies in AAPL's community"

**GraphRAG Enhancement:**
- Group companies by market segments
- Explain why companies are grouped together
- Suggest comparisons within the same community
- Identify sector-like groupings

---

## 4. FastRP Embeddings (`Company.embedding`)

### What It Is
128-dimensional vector embeddings that capture structural similarity in the graph. Can be used for semantic similarity search.

### GraphRAG Usage

**Query Pattern:**
```cypher
// Find companies with similar embeddings (cosine similarity)
MATCH (c1:Company {symbol: $symbol})
WHERE c1.embedding IS NOT NULL
MATCH (c2:Company)
WHERE c2.embedding IS NOT NULL AND c2.symbol <> c1.symbol
WITH c1, c2,
     gds.similarity.cosine(c1.embedding, c2.embedding) AS similarity
WHERE similarity > 0.7
RETURN c2.symbol, similarity
ORDER BY similarity DESC
LIMIT 5
```

**Example Questions:**
- "Find companies with similar graph structure to NVDA"
- "Which stocks have the most similar network position to TSLA?"
- "Show me companies with embeddings similar to GOOG"

**GraphRAG Enhancement:**
- Semantic similarity search beyond correlation
- Find structurally similar companies
- Explain graph-based relationships

---

## Integration with GraphRAG Prompts

### Enhanced Query Examples

Add these to your `prompts.py` few-shot examples:

```python
Example - Similarity Query:
Question: "Which companies are similar to AAPL?"
Query: MATCH (c1:Company {symbol: $symbol})-[r:GDS_SIMILAR]-(c2:Company)
      RETURN c2.symbol, r.score
      ORDER BY r.score DESC
      LIMIT 5

Example - Centrality Query:
Question: "What are the most influential companies?"
Query: MATCH (c:Company)
      WHERE c.pagerank IS NOT NULL
      RETURN c.symbol, c.pagerank
      ORDER BY c.pagerank DESC
      LIMIT 10

Example - Community Query:
Question: "What companies are in the same group as MSFT?"
Query: MATCH (c1:Company {symbol: $symbol})
      WHERE c1.community IS NOT NULL
      MATCH (c2:Company)
      WHERE c2.community = c1.community AND c2.symbol <> c1.symbol
      RETURN c2.symbol
```

### Enhanced Answer Prompts

Update `get_qa_prompt()` to handle GDS query types:

```python
elif query_type == "similarity":
    return f"""{base_prompt}
- Explain which companies are similar and why
- Mention similarity scores (higher = more similar)
- Suggest why they might be similar (sector, correlation patterns)
- Be concise and factual"""

elif query_type == "centrality":
    return f"""{base_prompt}
- Explain PageRank scores (higher = more influential)
- Rank companies by importance
- Explain what makes a company central in the network"""
```

---

## Query Type Detection

Add GDS query detection to `detect_query_type()`:

```python
def detect_query_type(question: str, query: str) -> str:
    question_lower = question.lower()
    query_upper = query.upper()
    
    # GDS query types
    if "GDS_SIMILAR" in query_upper or "similar" in question_lower:
        return "similarity"
    if "pagerank" in query_upper or "influential" in question_lower or "central" in question_lower:
        return "centrality"
    if "community" in query_upper or "group" in question_lower or "segment" in question_lower:
        return "community"
    
    # ... existing detection logic
```

---

## Best Practices

1. **Combine GDS with Domain Data:**
   - Use GDS outputs to enhance, not replace, price/performance queries
   - Combine PageRank with actual price data for richer answers

2. **Explain GDS Metrics:**
   - Always explain what GDS metrics mean (similarity, centrality, community)
   - Provide context (e.g., "high PageRank means central in correlation network")

3. **Use for Recommendations:**
   - Similarity scores → "You might also be interested in..."
   - Community detection → "Companies in the same sector..."
   - PageRank → "Most influential companies in the market..."

4. **Performance:**
   - GDS outputs are pre-computed, so queries are fast
   - Use embeddings for similarity search when correlation isn't enough

---

## Example GraphRAG Queries Using GDS

### 1. Similarity-Based Recommendation
```
User: "What companies are similar to AAPL?"
GraphRAG: Uses GDS_SIMILAR to find similar companies, explains similarity scores
```

### 2. Market Influence Analysis
```
User: "Which companies are most influential?"
GraphRAG: Uses PageRank to rank companies by network centrality
```

### 3. Sector Grouping
```
User: "What companies move together with MSFT?"
GraphRAG: Uses community detection to find companies in the same group
```

### 4. Structural Similarity
```
User: "Find companies with similar graph structure to NVDA"
GraphRAG: Uses embedding cosine similarity to find structurally similar companies
```

---

## Summary

GDS outputs enhance GraphRAG by:
- **Adding context**: Similarity, centrality, community membership
- **Enabling recommendations**: "You might also be interested in..."
- **Enriching answers**: Combine price data with network analysis
- **Enabling new query types**: Similarity, influence, grouping queries

All GDS outputs are pre-computed and ready to use in your GraphRAG pipeline!

