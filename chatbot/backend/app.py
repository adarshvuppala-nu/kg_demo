from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import time

from graph import run_cypher
from llm import explain, generate_cypher_query, extract_symbol_from_question
from prompts import EXTENDED_GRAPH_SCHEMA, GRAPH_SCHEMA, validate_cypher_query
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
    context: Optional[list] = None  # Full conversation history from frontend
    message_history: Optional[list] = None  # Previous messages in the chat window


# Health Check with connection validation
@app.get("/")
def health():
    try:
        from graph import validate_schema_connection
        is_connected = validate_schema_connection()
        return {
            "status": "ok" if is_connected else "degraded",
            "neo4j_connected": is_connected,
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "error", "message": str(e)}


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
        server_context = CONVERSATION_CONTEXT.get(conv_id, {})
        
        # Build rich context from multiple sources
        # 1. Server-side context (if exists)
        # 2. Frontend-provided message history (full chat window)
        frontend_history = req.message_history or req.context or []
        
        # 3. Merge into comprehensive context
        context = {
            **server_context,
            'message_history': frontend_history,  # Full chat history from frontend
            'conversation_id': conv_id,
            'last_question': server_context.get('last_question'),
            'last_answer': server_context.get('last_answer'),
            'last_symbol': server_context.get('last_symbol'),
            'last_query_type': server_context.get('last_query_type'),
            'last_query': server_context.get('last_query'),
        }
        
        # Extract recent context from message history if available
        if frontend_history and len(frontend_history) > 0:
            # Get last few messages for context
            recent_messages = frontend_history[-5:]  # Last 5 messages
            context['recent_messages'] = recent_messages
            
            # Extract symbols and topics from recent messages
            recent_symbols = []
            recent_topics = []
            for msg in recent_messages:
                msg_text = (msg.get('question', '') or msg.get('content', '') or '').lower()
                # Extract potential symbols
                for symbol in ["AAPL", "MSFT", "GOOG", "AMZN", "META", "NVDA", "TSLA", "JPM", "UNH", "BRK-B"]:
                    if symbol.lower() in msg_text or symbol in msg_text:
                        if symbol not in recent_symbols:
                            recent_symbols.append(symbol)
                # Extract topics
                if any(word in msg_text for word in ["compare", "comparison"]):
                    recent_topics.append("comparison")
                if any(word in msg_text for word in ["similar", "moves with"]):
                    recent_topics.append("similarity")
            
            context['recent_symbols'] = recent_symbols
            context['recent_topics'] = recent_topics
        
        last_symbol = context.get('last_symbol')
        last_query_type = context.get('last_query_type')
        
        # Step 0: Intelligent intent classification with LLM
        intent, intent_data = classify_intent(question, context)
        logger.info(f"Intent classified as: {intent} with context: {len(frontend_history)} messages")
        
        # Handle ONLY pure conversational intents (greetings, thanks) - everything else goes to GraphRAG
        if intent == "conversational":
            # Check if it's a greeting/thanks - only these get LLM direct answer
            question_lower = question.lower()
            is_greeting = any(word in question_lower for word in ["hello", "hi", "hey", "thanks", "thank you", "thx"])
            
            if is_greeting:
                # Pure greeting/thanks - answer with LLM directly
                answer = _answer_with_llm(question, context)
                
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
                    "is_followup": True,
                    "confidence": 0.85
                }
            # If not a greeting, continue to GraphRAG pipeline below
        
        # ALL other questions go through GraphRAG pipeline
        # This includes: data queries, clarifications, confirmations, general questions
        # We ALWAYS try to find data first, then format with LLM
        
        # Check if this is a followup question (short, references previous)
        is_followup = _is_followup_question(question, context)
        
        # Check if this is an explanation/clarification question about previous answer
        is_explanation_question = _is_explanation_question(question, context)
        
        # If it's an explanation question with previous context, explain methodology
        if is_explanation_question and context.get('last_query') and context.get('last_query_type'):
            try:
                explanation = _explain_methodology(question, context)
                if explanation:
                    # Update context
                    CONVERSATION_CONTEXT[conv_id] = {
                        **context,
                        'last_question': question,
                        'last_answer': explanation,
                        'timestamp': time.time()
                    }
                    return {
                        "answer": explanation,
                        "intent": "explanation",
                        "conversation_id": conv_id,
                        "is_followup": True,
                        "confidence": 0.85,
                        "processing_time_ms": int((time.time() - start_time) * 1000)
                    }
            except Exception as e:
                logger.error(f"Error explaining methodology: {str(e)}")
                # Fall through to normal query generation
        
        # Step 1: Generate Cypher query using LLM (with retry logic)
        query_start = time.time()
        cypher_query = None
        params = {}
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                # PRODUCTION-LEVEL: Always use LLM for intelligent query generation
                symbol = extract_symbol_from_question(question) or (last_symbol if is_followup else None)
                
                # Build comprehensive context with full conversation history
                enhanced_context = {
                    **context,
                    'extracted_symbol': symbol,
                    'is_followup': is_followup,
                    'last_symbol': last_symbol,
                    'last_query_type': last_query_type,
                    'message_history': context.get('message_history', []),
                    'recent_symbols': context.get('recent_symbols', []),
                    'recent_topics': context.get('recent_topics', [])
                }
                
                # Always use extended schema - LLM will use what it needs intelligently
                schema = EXTENDED_GRAPH_SCHEMA
                
                # Let LLM generate query with full conversation context
                cypher_query, params = generate_cypher_query(question, schema, context=enhanced_context)
                query_time = time.time() - query_start
                logger.info(f"LLM-generated query (attempt {attempt + 1}) with {len(context.get('message_history', []))} messages in context (took {query_time:.2f}s)")
                
                if cypher_query:
                    # Validate query before execution
                    is_valid, error_msg = validate_cypher_query(cypher_query)
                    if is_valid:
                        break
                    else:
                        logger.warning(f"Invalid query (attempt {attempt + 1}): {error_msg}")
                        if attempt == max_retries - 1:
                            return {
                                "answer": "I couldn't generate a valid query for your question. Please try rephrasing it.",
                                "error": "invalid_query",
                                "confidence": 0.0
                            }
                else:
                    if attempt == max_retries - 1:
                        return {
                            "answer": "I couldn't understand your question. Please ask about stock prices, for example: 'What is the latest price of MSFT?' or 'Compare Microsoft to Apple'.",
                            "error": "query_generation_failed",
                            "confidence": 0.0
                        }
            except Exception as e:
                logger.error(f"Error generating Cypher query (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "answer": "I'm having trouble processing your question. Please try rephrasing it.",
                        "error": "query_generation_error",
                        "confidence": 0.0
                    }
                time.sleep(0.5)  # Brief delay before retry

        # Step 2: Execute the generated query (with retry logic)
        db_start = time.time()
        data = None
        max_db_retries = 2
        
        for attempt in range(max_db_retries):
            try:
                logger.info(f"Executing generated Cypher query (attempt {attempt + 1}): {cypher_query[:100]}...")
                logger.info(f"With parameters: {params}")
                
                data = run_cypher(cypher_query, params if params else None)
                db_time = time.time() - db_start
                logger.info(f"Database query took {db_time:.2f}s")
                
                if data is not None:
                    break
            except Exception as e:
                logger.error(f"Neo4j query error (attempt {attempt + 1}): {str(e)}")
                if attempt == max_db_retries - 1:
                    return {
                        "answer": "I'm having trouble accessing the database right now. Please try again in a moment.",
                        "error": "database_error",
                        "generated_query": cypher_query,
                        "confidence": 0.0
                    }
                time.sleep(0.5)  # Brief delay before retry

        if not data:
            # No data found - provide helpful response but encourage data queries
            answer = f"I couldn't find any data matching your question in the database. "
            
            # Check if it's a stock-related question
            if _is_stock_related(question):
                answer += "The company ticker might not be in our database, or the question might need to be rephrased. "
                answer += "I can help you with stock prices for: AAPL, MSFT, GOOG, AMZN, META, NVDA, TSLA, JPM, UNH, BRK-B. "
                answer += "Try asking about prices, comparisons, trends, or correlations for these companies."
            else:
                answer += "I specialize in answering questions using data from our Neo4j graph database and PostgreSQL. "
                answer += "Please ask about stock prices, company comparisons, trends, or correlations. "
                answer += "For example: 'What is the latest price of MSFT?', 'Compare Microsoft to Apple', or 'Which stocks move together?'"
            
            return {
                "answer": answer,
                "error": "no_data_found",
                "generated_query": cypher_query,
                "confidence": 0.70
            }

        # Step 3: Generate natural language answer using LLM (with fallback)
        llm_start = time.time()
        query_type = _detect_query_type(question, cypher_query)
        
        try:
            # Pass conversation context for better understanding
            explanation = explain(question, data, query=cypher_query, query_type=query_type, context=context)
            llm_time = time.time() - llm_start
            logger.info(f"LLM response generation took {llm_time:.2f}s")
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Robust fallback - format data intelligently
            if data and len(data) > 0:
                try:
                    # Try to extract key information from data
                    sample = data[0]
                    if 'p.close' in sample or 'close' in str(sample):
                        price = sample.get('p.close') or sample.get('close')
                        date = sample.get('p.date') or sample.get('date')
                        explanation = f"I found data showing a price of ${price} on {date}."
                    elif 'c.symbol' in sample or 'symbol' in str(sample):
                        symbols = [d.get('c.symbol') or d.get('symbol') for d in data[:5]]
                        explanation = f"I found {len(data)} companies: {', '.join([s for s in symbols if s])}"
                    else:
                        explanation = f"I found {len(data)} result(s) in the database."
                except:
                    explanation = f"I found {len(data)} result(s) in the database."
            else:
                explanation = "I found data but couldn't generate a proper explanation."

        # Update conversation context (enhanced with better tracking)
        symbol = params.get('symbol') if params else extract_symbol_from_question(question)
        query_type = _detect_query_type(question, cypher_query)
        
        # Enhanced context tracking for better conversation flow
        
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
            "raw_data": data[:10] if data else [],  # Limit data size for response
            "generated_query": cypher_query,
            "conversation_id": conv_id,
            "is_followup": is_followup,
            "intent": "data_query",
            "confidence": confidence,
            "query_type": query_type,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        # Don't crash - return error response
        return {
            "answer": "I encountered an unexpected error. Please try again or rephrase your question.",
            "error": "internal_error",
            "confidence": 0.0,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }

# Helper functions for intelligent chatbot behavior
def _needs_stock_data(question: str, context: dict) -> bool:
    """
    Determine if question needs stock data from Neo4j.
    Returns True if GraphRAG is needed, False if LLM can answer directly.
    """
    question_lower = question.lower()
    
    # Stock data indicators
    stock_indicators = [
        "price", "stock", "share", "ticker", "company", "trading", "volume",
        "close", "open", "high", "low", "adj close", "adj_close",
        "outperform", "compare", "trend", "correlat", "similar", "influential",
        "pagerank", "community", "group", "vs", "versus", "better", "worse",
        "moves with", "moves together", "performance", "return"
    ]
    
    # Company names or tickers
    companies = ["apple", "microsoft", "amazon", "google", "meta", "facebook",
                "nvidia", "tesla", "jpmorgan", "unitedhealth", "berkshire",
                "aapl", "msft", "goog", "amzn", "meta", "nvda", "tsla", "jpm", "unh", "brk"]
    
    # Check if question is about stocks
    if any(indicator in question_lower for indicator in stock_indicators):
        return True
    
    if any(company in question_lower for company in companies):
        return True
    
    # Check context - if previous question was about stocks
    if context.get('recent_topics'):
        if 'comparison' in context.get('recent_topics', []) or 'similarity' in context.get('recent_topics', []):
            return True
    
    return False

def _is_stock_related(question: str) -> bool:
    """Check if question is stock-related."""
    return _needs_stock_data(question, {})

def _answer_with_llm(question: str, context: dict) -> str:
    """
    Answer question using LLM directly (ChatGPT-like).
    Used for general questions, explanations, or when no data is needed.
    """
    from llm import client
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not client:
        return "I'm here to help with stock price information. Please ask me about stock prices, for example: 'What is the latest price of MSFT?'"
    
    try:
        # Build context from conversation history
        context_text = ""
        if context.get('message_history'):
            recent = context.get('message_history', [])[-3:]
            if recent:
                context_text = "\n\nRecent conversation:\n"
                for msg in recent:
                    q = msg.get('question', msg.get('content', ''))
                    a = msg.get('answer', '')
                    if q:
                        context_text += f"User: {q}\n"
                    if a:
                        context_text += f"Assistant: {a[:100]}...\n"
        
        prompt = f"""You are a helpful and intelligent financial assistant chatbot. Answer the user's question naturally and conversationally.

User Question: {question}
{context_text}

Instructions:
- Be helpful, friendly, and conversational (like ChatGPT)
- If the question is about stock prices, companies, or financial data, mention that you can help with data from the database
- If it's a general question, answer it naturally
- If it's a follow-up question, reference the previous conversation
- Be concise but informative
- If you don't know something, say so honestly

Answer:"""
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # More creative for conversational responses
            max_tokens=300,
            timeout=15.0
        )
        
        return resp.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"LLM answer generation error: {str(e)}")
        return "I'm here to help with stock price information. Please ask me about stock prices, for example: 'What is the latest price of MSFT?'"

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

def _is_explanation_question(question: str, context: dict) -> bool:
    """Detect if question is asking for explanation/clarification about previous answer."""
    if not context or not context.get('last_query'):
        return False
    
    question_lower = question.lower()
    
    # Explanation question indicators
    explanation_indicators = [
        'how is that', 'how was that', 'how does that', 'how do you',
        'what factors', 'what method', 'how calculated', 'how computed',
        'why', 'explain', 'tell me more about', 'what does that mean',
        'how does it work', 'how did you', 'how can you'
    ]
    
    # Check if question contains explanation indicators
    if any(indicator in question_lower for indicator in explanation_indicators):
        return True
    
    # Short questions with "how" or "what" after a data query are likely explanations
    if len(question.split()) <= 5:
        if question_lower.startswith(('how', 'what', 'why')):
            return True
    
    return False

def _explain_methodology(question: str, context: dict) -> Optional[str]:
    """Explain methodology based on previous query and data."""
    from llm import client
    
    if not client:
        return None
    
    last_query = context.get('last_query', '')
    last_query_type = context.get('last_query_type', '')
    last_answer = context.get('last_answer', '')
    last_data_count = context.get('last_data_count', 0)
    
    # Build methodology explanation based on query type
    methodology_info = ""
    
    if 'GDS_SIMILAR' in last_query or last_query_type == 'similarity':
        methodology_info = """
The similarity scores are calculated using Neo4j Graph Data Science (GDS) Node Similarity algorithm.

How it works:
1. The algorithm analyzes the graph structure and relationships between companies
2. It uses the GDS_SIMILAR relationships which were created by running the Node Similarity algorithm
3. The similarity score (0.0 to 1.0) indicates how similar two companies are based on their graph connections
4. Higher scores (closer to 1.0) mean companies are more similar in their market behavior
5. The algorithm considers factors like:
   - Shared relationships in the graph
   - Common patterns in stock price movements
   - Structural similarities in the knowledge graph

The scores you see (e.g., 0.78) represent the strength of similarity between companies.
"""
    elif 'PERFORMED_IN' in last_query or last_query_type == 'comparison':
        methodology_info = """
The comparison is based on the PERFORMED_IN relationships in the Neo4j graph.

How it works:
1. Each company has PERFORMED_IN relationships to Year nodes
2. These relationships contain return_pct (return percentage) for each year
3. The comparison uses these return percentages to compare performance
4. If return_pct is None, it means that performance data is not available in the database for that period
"""
    elif 'CORRELATED_WITH' in last_query or last_query_type == 'correlation':
        methodology_info = """
The correlation is calculated using the CORRELATED_WITH relationships.

How it works:
1. The system calculates Pearson correlation between daily returns of company pairs
2. Only correlations with absolute value >= 0.3 and at least 30 common trading days are stored
3. The correlation value ranges from -1.0 (perfect negative correlation) to +1.0 (perfect positive correlation)
4. Positive values mean stocks move together, negative means they move in opposite directions
"""
    elif 'pagerank' in last_query.lower() or last_query_type == 'pagerank':
        methodology_info = """
PageRank is calculated using Neo4j Graph Data Science (GDS) PageRank algorithm.

How it works:
1. PageRank measures the importance/influence of companies in the graph
2. Companies with more connections and relationships have higher PageRank scores
3. The algorithm considers both direct and indirect connections
4. Higher PageRank indicates greater influence in the market network
"""
    elif 'community' in last_query.lower() or last_query_type == 'community':
        methodology_info = """
Community detection uses Neo4j Graph Data Science (GDS) Louvain algorithm.

How it works:
1. The Louvain algorithm groups companies into communities based on graph structure
2. Companies in the same community have similar patterns of relationships
3. This helps identify market segments or sectors
4. Companies in the same community often have correlated stock movements
"""
    else:
        methodology_info = f"""
The data was retrieved using this Neo4j Cypher query:
{last_query}

The query returned {last_data_count} result(s) from the graph database.
"""
    
    try:
        prompt = f"""You are a helpful financial assistant. The user is asking about how a previous calculation or result was determined.

Previous Question: {context.get('last_question', 'N/A')}
Previous Answer: {last_answer[:200]}...

Current Question: {question}

Methodology Information:
{methodology_info}

Instructions:
- Explain how the previous result was calculated in a clear, conversational way
- Reference the specific algorithm or method used
- Be concise but informative
- Use the methodology information provided above
- If the question is about "what factors", explain what factors the algorithm considers

Answer:"""
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
            timeout=15.0
        )
        
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error explaining methodology: {str(e)}")
        return None

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