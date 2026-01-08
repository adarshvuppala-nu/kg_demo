#!/usr/bin/env python3
"""
Production-ready chatbot test suite.
Tests various question types and edge cases.
"""

import requests
import json
import time
from typing import List, Dict

BASE_URL = "http://localhost:8000"

def test_question(question: str, expected_keywords: List[str] = None) -> Dict:
    """Test a single question and return results."""
    print(f"\n{'='*60}")
    print(f"Testing: {question}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"question": question},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # Check for errors
        if "error" in data and data["error"] not in ["no_data_found"]:
            print(f"❌ Error: {data.get('error')}")
            print(f"   Answer: {data.get('answer', '')[:100]}")
            return {"success": False, "data": data}
        
        # Check answer quality
        answer = data.get("answer", "")
        if not answer:
            print(f"❌ No answer provided")
            return {"success": False, "data": data}
        
        # Check for expected keywords
        if expected_keywords:
            found = [kw for kw in expected_keywords if kw.lower() in answer.lower()]
            if not found:
                print(f"⚠️  Expected keywords not found: {expected_keywords}")
        
        # Check if GraphRAG was used
        has_query = "generated_query" in data and data["generated_query"]
        has_data = "raw_data" in data
        
        print(f"✅ Answer: {answer[:150]}...")
        print(f"   Confidence: {data.get('confidence', 0):.0%}")
        print(f"   Has Query: {has_query}")
        print(f"   Has Data: {has_data}")
        print(f"   Processing: {data.get('processing_time_ms', 0)}ms")
        
        return {
            "success": True,
            "data": data,
            "has_query": has_query,
            "has_data": has_data
        }
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Backend not running?")
        return {"success": False, "error": "connection_error"}
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"success": False, "error": str(e)}

def run_test_suite():
    """Run comprehensive test suite."""
    print("\n" + "="*60)
    print("PRODUCTION CHATBOT TEST SUITE")
    print("="*60)
    
    tests = [
        # Basic queries
        ("What companies are in the database?", ["company", "database"]),
        ("What is the latest price of AAPL?", ["price", "AAPL"]),
        ("What is the price of MSFT?", ["price", "MSFT"]),
        ("Show me Apple stock price", ["Apple", "price"]),
        
        # Comparisons
        ("Compare Microsoft to Apple", ["Microsoft", "Apple", "compare"]),
        ("Compare MSFT to AAPL", ["MSFT", "AAPL"]),
        ("compare nvidia to apple", ["NVIDIA", "Apple"]),
        
        # Follow-up questions
        ("What is the latest price of AAPL?", None),
        ("What about Microsoft?", ["Microsoft"]),
        ("How about Google?", ["Google"]),
        
        # GDS queries
        ("Which stocks move with MSFT?", ["move", "MSFT"]),
        ("What stocks are similar to Apple?", ["similar", "Apple"]),
        ("Which companies are in the same group as AAPL?", ["group", "AAPL"]),
        
        # Edge cases
        ("", None),  # Empty question
        ("hello", None),  # Greeting
        ("What is a stock?", None),  # General question
        ("xyz123", None),  # Nonsense
    ]
    
    results = []
    for question, keywords in tests:
        result = test_question(question, keywords)
        results.append(result)
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r.get("success"))
    total = len(results)
    
    print(f"Successful: {successful}/{total} ({successful/total*100:.0f}%)")
    print(f"Failed: {total - successful}/{total}")
    
    # Check GraphRAG usage
    graphrag_used = sum(1 for r in results if r.get("has_query"))
    print(f"GraphRAG queries: {graphrag_used}/{total}")
    
    return results

if __name__ == "__main__":
    run_test_suite()

