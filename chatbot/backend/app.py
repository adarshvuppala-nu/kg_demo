from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import time

from graph import run_cypher
from llm import explain, generate_cypher_query, extract_symbol_from_question
from prompts import EXTENDED_GRAPH_SCHEMA, GRAPH_SCHEMA
from intent_classifier import classify_intent, handle_conversational_intent

# In-memory conversation context cache (in production, use Redis or similar)
CONVERSATION_CONTEXT = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="S&P Knowledge Graph Chatbot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None  # For tracking conversations
    context: Optional[list] = None  # Previous messages for context


# Health Check
@app.get("/")
def health():
    return {"status": "ok"}


# Chat Endpoint (GraphRAG with LLM-generated queries)
@app.post("/chat")
def chat(req: ChatRequest):
    start_time = time.time()
    try:
        question = req.question.strip()
        
        if not question:
            return {
                "answer": "I'm here to help! Please ask me a question about stock prices.",
                "error": "empty_question"
            }

        logger.info(f"Processing question: {question}")

        # Get conversation context for followups
        conv_id = req.conversation_id or "default"
        context = CONVERSATION_CONTEXT.get(conv_id, {})
        last_symbol = context.get('last_symbol')
        last_query_type = context.get('last_query_type')
        
        # Step 0: Classify intent (conversational vs data query)
        intent, intent_data = classify_intent(question, context)
        logger.info(f"Intent classified as: {intent}")
        
        # Handle conversational intents directly (no database query needed)
        if intent in ["conversational", "clarification", "confirmation"]:
            answer = handle_conversational_intent(question, intent_data, context)
            
            # Update context
            CONVERSATION_CONTEXT[conv_id] = {
                **context,
                'last_question': question,
                'last_answer': answer,
                'timestamp': time.time()
            }
            
            return {
                "answer": answer,
                "intent": intent,
                "conversation_id": conv_id,
                "is_followup": True
            }
        
        # Check if this is a followup question (short, references previous)
        is_followup = _is_followup_question(question, context)
        
        # Step 1: Generate Cypher query using LLM (with caching and followup optimization)
        query_start = time.time()
        cypher_query = None
        params = {}
        
        try:
            # Extract symbol first - if we have one, we can generate a simple query
            symbol = extract_symbol_from_question(question) or (last_symbol if is_followup else None)
            
            # Fast path: If we have a symbol, generate query directly
            # Check if it's a simple price question OR if we have a known company name
            question_lower = question.lower()
            is_simple_price_query = any(word in question_lower for word in [
                "price", "latest", "current", "stock", "share", "close", "open", "high", "low",
                "what", "show", "tell", "get", "give", "find"
            ])
            
            # If we have a symbol and it looks like a stock question, generate query directly
            if symbol and (is_simple_price_query or symbol in ["AAPL", "MSFT", "GOOG", "AMZN", "META", "NVDA", "TSLA", "JPM", "UNH", "BRK-B"]):
                # Generate simple query directly without LLM
                cypher_query = "MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay) RETURN p.date, p.close, p.volume, p.open, p.high, p.low ORDER BY p.date DESC LIMIT 1"
                params = {"symbol": symbol}
                query_time = time.time() - query_start
                logger.info(f"Generated simple query for symbol: {symbol} (took {query_time:.2f}s)")
            else:
                # For followups, try to reuse context
                if is_followup and last_symbol:
                    symbol = symbol or last_symbol
                    logger.info(f"Followup detected, using context. Symbol: {symbol}")
                    
                    # Fast path: reuse query pattern for same type of question
                    if last_query_type == "price" and symbol:
                        cypher_query = "MATCH (c:Company {symbol: $symbol})-[:HAS_PRICE]->(p:PriceDay) RETURN p.date, p.close, p.volume ORDER BY p.date DESC LIMIT 1"
                        params = {"symbol": symbol}
                        query_time = 0.0  # Instant for cached pattern
                        logger.info("Using cached query pattern for followup")
                    else:
                        # Generate new query but with context (use extended schema for complex queries)
                        question_lower = question.lower()
                        is_complex = any(word in question_lower for word in [
                            "outperform", "compare", "trend", "correlat", "similar", "influential",
                            "pagerank", "community", "group", "vs", "versus", "better", "worse"
                        ])
                        schema = EXTENDED_GRAPH_SCHEMA if is_complex else GRAPH_SCHEMA
                        cypher_query, params = generate_cypher_query(question, schema, context=context)
                        query_time = time.time() - query_start
                        logger.info(f"Query generation took {query_time:.2f}s")
                else:
                    # Regular query generation (use extended schema for complex queries)
                    question_lower = question.lower()
                    is_complex = any(word in question_lower for word in [
                        "outperform", "compare", "trend", "correlat", "similar", "influential",
                        "pagerank", "community", "group", "vs", "versus", "better", "worse"
                    ])
                    schema = EXTENDED_GRAPH_SCHEMA if is_complex else GRAPH_SCHEMA
                    cypher_query, params = generate_cypher_query(question, schema, context=context)
                    query_time = time.time() - query_start
                    logger.info(f"Query generation took {query_time:.2f}s")
            
            if not cypher_query:
                return {
                    "answer": "I couldn't understand your question. Please ask about stock prices, for example: 'What is the latest price of MSFT?' or 'Show me the price of AAPL'.",
                    "error": "invalid_question"
                }
        except Exception as e:
            logger.error(f"Error generating Cypher query: {str(e)}")
            return {
                "answer": "I'm having trouble processing your question. Please try rephrasing it.",
                "error": "query_generation_error",
                "details": str(e)
            }

        # Step 2: Execute the generated query
        db_start = time.time()
        try:
            logger.info(f"Executing generated Cypher query: {cypher_query}")
            logger.info(f"With parameters: {params}")
            
            data = run_cypher(cypher_query, params if params else None)
            db_time = time.time() - db_start
            logger.info(f"Database query took {db_time:.2f}s")
        except Exception as e:
            logger.error(f"Neo4j query error: {str(e)}")
            return {
                "answer": "I'm having trouble accessing the database right now. Please try again in a moment.",
                "error": "database_error",
                "details": str(e),
                "generated_query": cypher_query
            }

        if not data:
            return {
                "answer": "I couldn't find any data matching your question. The company ticker might not be in our database, or the question might need to be rephrased.",
                "error": "no_data_found",
                "generated_query": cypher_query
            }

        # Step 3: Generate natural language answer using LLM
        llm_start = time.time()
        try:
            explanation = explain(question, data, query=cypher_query)
            llm_time = time.time() - llm_start
            logger.info(f"LLM response generation took {llm_time:.2f}s")
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Fallback to basic response if LLM fails
            if data and len(data) > 0:
                # Try to format the data nicely
                explanation = f"I found the following data: {data}"
            else:
                explanation = "I found data but couldn't generate a proper explanation."
            
            return {
                "answer": explanation,
                "warning": "llm_fallback",
                "raw_data": data,
                "generated_query": cypher_query
            }

        # Update conversation context (enhanced)
        symbol = params.get('symbol') if params else extract_symbol_from_question(question)
        query_type = _detect_query_type(question, cypher_query)
        
        # Enhanced context with more information
        CONVERSATION_CONTEXT[conv_id] = {
            'last_symbol': symbol,
            'last_query_type': query_type,
            'last_question': question,
            'last_answer': explanation,
            'last_query': cypher_query,
            'last_data_count': len(data) if data else 0,
            'timestamp': time.time(),
            'message_history': context.get('message_history', []) + [
                {'question': question, 'answer': explanation[:200], 'timestamp': time.time()}
            ][-5:]  # Keep last 5 messages
        }
        
        # Clean old contexts (older than 1 hour)
        _clean_old_contexts()

        total_time = time.time() - start_time
        logger.info(f"Total request processing took {total_time:.2f}s")

        # Calculate confidence score based on data quality and query complexity
        confidence = _calculate_confidence(data, cypher_query, question)
        
        return {
            "answer": explanation,
            "raw_data": data,
            "generated_query": cypher_query,  # Show query trace to users
            "conversation_id": conv_id,
            "is_followup": is_followup,
            "intent": "data_query",
            "confidence": confidence,
            "query_type": query_type,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Helper functions for conversation context
def _is_followup_question(question: str, context: dict) -> bool:
    """Detect if question is a followup to previous conversation."""
    if not context:
        return False
    
    question_lower = question.lower()
    
    # Short questions are often followups
    if len(question.split()) <= 4:
        # Check for followup indicators
        followup_indicators = [
            'what about', 'how about', 'and', 'also', 'tell me more',
            'what is', 'show me', 'give me', 'what\'s', 'whats'
        ]
        if any(indicator in question_lower for indicator in followup_indicators):
            return True
    
    # Questions without explicit symbol when we have context
    if context.get('last_symbol'):
        symbol = extract_symbol_from_question(question)
        if not symbol and ('price' in question_lower or 'stock' in question_lower):
            return True
    
    return False

def _detect_query_type(question: str, query: str) -> str:
    """Detect the type of query for context."""
    from prompts import detect_query_type as detect_type
    return detect_type(question, query)

def _clean_old_contexts():
    """Remove conversation contexts older than 1 hour."""
    current_time = time.time()
    to_remove = []
    for conv_id, ctx in CONVERSATION_CONTEXT.items():
        if current_time - ctx.get('timestamp', 0) > 3600:  # 1 hour
            to_remove.append(conv_id)
    for conv_id in to_remove:
        del CONVERSATION_CONTEXT[conv_id]

def _calculate_confidence(data: list, query: str, question: str) -> float:
    """
    Calculate confidence score (0.0 to 1.0) based on:
    - Data quality and completeness
    - Query complexity
    - Question clarity
    """
    if not data or len(data) == 0:
        return 0.0
    
    confidence = 0.5  # Base confidence
    
    # Data quality factors
    data_size = len(data)
    if data_size > 0:
        confidence += 0.2  # Has data
    if data_size > 10:
        confidence += 0.1  # Substantial data
    
    # Check data completeness (has required fields)
    sample = data[0] if data else {}
    required_fields = ['p.close', 'p.date']
    has_required = all(field in str(sample) or any(k.endswith('close') or k.endswith('date') for k in sample.keys()) for field in required_fields)
    if has_required:
        confidence += 0.1
    
    # Query complexity (simpler queries = higher confidence)
    query_upper = query.upper() if query else ""
    if "MATCH" in query_upper and query_upper.count("MATCH") == 1:
        confidence += 0.05  # Simple single-hop query
    elif query_upper.count("MATCH") > 1:
        confidence += 0.02  # Multi-hop query (slightly lower confidence)
    
    # Question clarity
    question_lower = question.lower()
    if any(word in question_lower for word in ["latest", "current", "now", "today"]):
        confidence += 0.05  # Clear temporal reference
    
    # Cap at 1.0
    return min(confidence, 1.0)