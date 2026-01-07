#!/usr/bin/env python3
"""
Test GDS Insights in GraphRAG
==============================
Demonstrates how GDS outputs improve GraphRAG answers.

Tests:
1. Node Similarity queries
2. PageRank centrality queries
3. Community detection queries
4. Embedding similarity queries
"""

from graph import run_cypher
from llm import explain, generate_cypher_query
from prompts import EXTENDED_GRAPH_SCHEMA
import os
from dotenv import load_dotenv

load_dotenv('/Users/adarshvuppala/kg_demo/.env')

def test_gds_similarity():
    """Test Node Similarity insights."""
    print("=" * 60)
    print("TEST 1: Node Similarity (GDS_SIMILAR)")
    print("=" * 60)
    
    # Direct GDS query
    print("\n📊 Direct GDS Query:")
    query = """
    MATCH (c1:Company {symbol: 'AAPL'})-[r:GDS_SIMILAR]-(c2:Company)
    RETURN c2.symbol AS company, r.score AS similarity_score
    ORDER BY r.score DESC
    LIMIT 5
    """
    result = run_cypher(query)
    print("   Similar companies to AAPL:")
    for r in result:
        print(f"      {r['company']}: {r['similarity_score']:.4f}")
    
    # GraphRAG question
    print("\n💬 GraphRAG Question: 'Which companies are similar to AAPL?'")
    question = "Which companies are similar to AAPL?"
    try:
        cypher, params = generate_cypher_query(question, EXTENDED_GRAPH_SCHEMA)
        if cypher:
            print(f"   Generated Cypher: {cypher[:150]}...")
            data = run_cypher(cypher, params)
            answer = explain(question, data, query=cypher)
            print(f"   GraphRAG Answer: {answer}\n")
        else:
            print("   ⚠️  Could not generate query (may need prompt update)")
    except Exception as e:
        print(f"   ⚠️  GraphRAG query generation: {str(e)[:100]}")

def test_gds_pagerank():
    """Test PageRank insights."""
    print("=" * 60)
    print("TEST 2: PageRank Centrality")
    print("=" * 60)
    
    # Direct GDS query
    print("\n📊 Direct GDS Query:")
    query = """
    MATCH (c:Company)
    WHERE c.pagerank IS NOT NULL
    RETURN c.symbol, c.pagerank
    ORDER BY c.pagerank DESC
    LIMIT 5
    """
    result = run_cypher(query)
    print("   Most influential companies (PageRank):")
    for r in result:
        print(f"      {r['c.symbol']}: {r['c.pagerank']:.6f}")
    
    # GraphRAG question
    print("\n💬 GraphRAG Question: 'What are the most influential companies?'")
    question = "What are the most influential companies in the market?"
    try:
        cypher, params = generate_cypher_query(question, EXTENDED_GRAPH_SCHEMA)
        if cypher:
            print(f"   Generated Cypher: {cypher[:150]}...")
            data = run_cypher(cypher, params)
            answer = explain(question, data, query=cypher)
            print(f"   GraphRAG Answer: {answer}\n")
        else:
            print("   ⚠️  Could not generate query")
    except Exception as e:
        print(f"   ⚠️  GraphRAG query generation: {str(e)[:100]}")

def test_gds_community():
    """Test Community Detection insights."""
    print("=" * 60)
    print("TEST 3: Community Detection")
    print("=" * 60)
    
    # Direct GDS query
    print("\n📊 Direct GDS Query:")
    query = """
    MATCH (c1:Company {symbol: 'AAPL'})
    WHERE c1.community IS NOT NULL
    MATCH (c2:Company)
    WHERE c2.community = c1.community AND c2.symbol <> c1.symbol
    RETURN c2.symbol
    ORDER BY c2.symbol
    """
    result = run_cypher(query)
    print("   Companies in AAPL's community:")
    companies = [r['c2.symbol'] for r in result]
    print(f"      {', '.join(companies)}")
    
    # GraphRAG question
    print("\n💬 GraphRAG Question: 'What companies are in the same group as AAPL?'")
    question = "What companies are in the same community as AAPL?"
    try:
        cypher, params = generate_cypher_query(question, EXTENDED_GRAPH_SCHEMA)
        if cypher:
            print(f"   Generated Cypher: {cypher[:150]}...")
            data = run_cypher(cypher, params)
            answer = explain(question, data, query=cypher)
            print(f"   GraphRAG Answer: {answer}\n")
        else:
            print("   ⚠️  Could not generate query")
    except Exception as e:
        print(f"   ⚠️  GraphRAG query generation: {str(e)[:100]}")

def test_gds_embedding():
    """Test FastRP Embedding similarity."""
    print("=" * 60)
    print("TEST 4: FastRP Embedding Similarity")
    print("=" * 60)
    
    # Direct GDS query
    print("\n📊 Direct GDS Query (Cosine Similarity):")
    query = """
    MATCH (c1:Company {symbol: 'AAPL'})
    WHERE c1.embedding IS NOT NULL
    MATCH (c2:Company)
    WHERE c2.embedding IS NOT NULL AND c2.symbol <> c1.symbol
    WITH c1, c2, gds.similarity.cosine(c1.embedding, c2.embedding) AS similarity
    WHERE similarity > 0.7
    RETURN c2.symbol, similarity
    ORDER BY similarity DESC
    LIMIT 5
    """
    try:
        result = run_cypher(query)
        print("   Companies with similar embeddings to AAPL:")
        for r in result:
            print(f"      {r['c2.symbol']}: {r['similarity']:.4f}")
    except Exception as e:
        print(f"   ⚠️  Embedding similarity query: {str(e)[:80]}")

def compare_without_gds():
    """Compare answers with and without GDS."""
    print("=" * 60)
    print("TEST 5: Comparison - With vs Without GDS")
    print("=" * 60)
    
    question = "Which companies are similar to TSLA?"
    
    # Without GDS (using CORRELATED_WITH only)
    print("\n📊 Without GDS (CORRELATED_WITH only):")
    query1 = """
    MATCH (c1:Company {symbol: 'TSLA'})-[r:CORRELATED_WITH]-(c2:Company)
    RETURN c2.symbol, r.correlation
    ORDER BY ABS(r.correlation) DESC
    LIMIT 5
    """
    result1 = run_cypher(query1)
    print("   Results:")
    for r in result1:
        print(f"      {r['c2.symbol']}: correlation {r['r.correlation']:.4f}")
    
    # With GDS (using GDS_SIMILAR)
    print("\n📊 With GDS (GDS_SIMILAR):")
    query2 = """
    MATCH (c1:Company {symbol: 'TSLA'})-[r:GDS_SIMILAR]-(c2:Company)
    RETURN c2.symbol, r.score
    ORDER BY r.score DESC
    LIMIT 5
    """
    result2 = run_cypher(query2)
    print("   Results:")
    for r in result2:
        print(f"      {r['c2.symbol']}: similarity {r['r.score']:.4f}")
    
    print("\n💡 Insight: GDS_SIMILAR captures structural similarity,")
    print("   while CORRELATED_WITH captures price movement correlation.")
    print("   They provide complementary insights!")

def show_graphrag_flow():
    """Show how GraphRAG uses Neo4j and GDS."""
    print("\n" + "=" * 60)
    print("GRAPHRAG FLOW: How It Uses Neo4j & GDS")
    print("=" * 60)
    
    question = "Which companies are most similar to NVDA and why?"
    
    print(f"\n1️⃣  User Question: '{question}'")
    
    print("\n2️⃣  LLM Generates Cypher Query:")
    try:
        cypher, params = generate_cypher_query(question, EXTENDED_GRAPH_SCHEMA)
        if cypher:
            print(f"   {cypher}")
            
            print("\n3️⃣  Neo4j Executes Query (uses GDS_SIMILAR relationships):")
            data = run_cypher(cypher, params)
            print(f"   Retrieved {len(data)} results from graph")
            for i, r in enumerate(data[:3], 1):
                print(f"   {i}. {r}")
            
            print("\n4️⃣  LLM Synthesizes Answer from Graph Data:")
            answer = explain(question, data, query=cypher)
            print(f"   {answer}")
        else:
            print("   ⚠️  Query generation failed")
    except Exception as e:
        print(f"   ⚠️  Error: {str(e)[:100]}")
    
    print("\n💡 Key Points:")
    print("   • GraphRAG queries Neo4j graph (not LLM knowledge)")
    print("   • GDS outputs (GDS_SIMILAR, PageRank, Community) enrich the graph")
    print("   • LLM only formats the graph data into natural language")
    print("   • This prevents hallucination - answers come from real data")

def main():
    """Run all GDS insight tests."""
    print("\n" + "=" * 60)
    print("GDS INSIGHTS TESTING FOR GRAPHRAG")
    print("=" * 60)
    
    test_gds_similarity()
    test_gds_pagerank()
    test_gds_community()
    test_gds_embedding()
    compare_without_gds()
    show_graphrag_flow()
    
    print("\n" + "=" * 60)
    print("✅ GDS INSIGHTS TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

