from openai import OpenAI
import os
import logging
import re
from functools import lru_cache
from typing import Optional, Tuple
from prompts import (
    get_cypher_generation_prompt, 
    get_qa_prompt, 
    validate_cypher_query, 
    detect_query_type,
    EXTENDED_GRAPH_SCHEMA
)

logger = logging.getLogger(__name__)

# Initialize client only if API key is available
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key, timeout=30.0)  # Add timeout
else:
    client = None
    logger.warning("OPENAI_API_KEY not found in environment variables")

# Cache for common query patterns
QUERY_CACHE = {}

def explain(question: str, data: list, query: Optional[str] = None, query_type: str = "general", context: Optional[dict] = None) -> str:
    """
    Generate a natural language explanation using OpenAI.
    Enhanced with query-type detection and context awareness for better responses.
    
    Args:
        question: Original user question
        data: Query results (list of dicts)
        query: Cypher query that generated the data (optional, for query type detection)
        query_type: Type of query (general, trend, comparison, correlation, similarity, etc.)
        context: Optional conversation context for better understanding
    
    Returns:
        Natural language answer
    """
    if not client:
        logger.warning("OpenAI client not initialized, using fallback response")
        if data and len(data) > 0:
            price_data = data[0]
            # Format date properly
            date_val = price_data.get('p.date')
            if hasattr(date_val, 'year'):
                date_str = f"{date_val.year}-{date_val.month:02d}-{date_val.day:02d}"
            else:
                date_str = str(date_val)
            
            close = price_data.get('p.close', 'N/A')
            volume = price_data.get('p.volume', 'N/A')
            open_price = price_data.get('p.open')
            high = price_data.get('p.high')
            low = price_data.get('p.low')
            
            answer = f"The latest price on {date_str} was ${close:.2f}" if isinstance(close, (int, float)) else f"The latest price on {date_str} was ${close}"
            
            if open_price and high and low:
                answer += f". Opening: ${open_price:.2f}, High: ${high:.2f}, Low: ${low:.2f}"
            
            if volume and isinstance(volume, (int, float)):
                answer += f". Volume: {int(volume):,} shares"
            
            return answer
        return "Unable to generate explanation (OpenAI API not configured)."
    
    try:
        # Use provided query_type or detect it
        if query_type == "general":
            query_type = detect_query_type(question, query or "")
        
        # Use enhanced QA prompt based on query type with context
        prompt = get_qa_prompt(question, data, query_type, context=context)
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,  # Increased for trend/comparison queries
            timeout=15.0
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        # Fallback response
        if data and len(data) > 0:
            price_data = data[0]
            return f"The latest price for the stock was ${price_data.get('p.close', 'N/A')} on {price_data.get('p.date', 'N/A')}."
        raise

def _normalize_question(question: str) -> str:
    """Normalize question for caching."""
    # Remove extra spaces, lowercase, remove punctuation
    normalized = re.sub(r'[^\w\s]', '', question.lower().strip())
    normalized = ' '.join(normalized.split())
    return normalized

def generate_cypher_query(question: str, schema_prompt: str, context: Optional[dict] = None) -> Tuple[Optional[str], dict]:
    """
    Generate a Cypher query from natural language using LLM.
    Includes caching for common queries.
    Returns (cypher_query, parameters_dict)
    """
    if not client:
        logger.warning("OpenAI client not initialized, cannot generate Cypher query")
        return None, {}
    
    # Check cache first
    normalized_q = _normalize_question(question)
    cache_key = f"{normalized_q}"
    
    if cache_key in QUERY_CACHE:
        logger.info(f"Using cached query for: {question[:50]}")
        cached_query, cached_params_template = QUERY_CACHE[cache_key]
        # Re-extract parameters for this specific question
        if cached_query is None:
            logger.warning("Cached query is None, regenerating...")
            # Fall through to regenerate
        else:
            params = extract_query_parameters(question, cached_query, context)
            return cached_query, params
    
    try:
        # Add context if available for followups
        context_hint = ""
        if context and context.get('last_symbol'):
            context_hint = f"\nContext: Previous question was about {context.get('last_symbol')}. If question doesn't specify symbol, use {context.get('last_symbol')}."
        
        # Use schema-safe prompt from prompts module with full context
        prompt = get_cypher_generation_prompt(question, use_extended=True, context=context)
        if context_hint:
            prompt += f"\n\nAdditional Context: {context_hint}"
        
        # Add conversation history for better context
        if context and context.get('message_history'):
            history = context.get('message_history', [])[-3:]  # Last 3 messages
            if history:
                try:
                    history_text = "\n".join([
                        f"Q: {m.get('question', '') if isinstance(m, dict) else ''} A: {m.get('answer', '')[:50] if isinstance(m, dict) and m.get('answer') else ''}..." 
                        for m in history if isinstance(m, dict)
                    ])
                    if history_text.strip():
                        prompt += f"\n\nPrevious conversation:\n{history_text}"
                except Exception as e:
                    logger.warning(f"Error processing message history: {str(e)}")
                    # Continue without history if there's an error
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=250,  # Increased for complex queries
            timeout=15.0  # More time for complex queries
        )
        
        query = resp.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        query = re.sub(r'```cypher\n?', '', query)
        query = re.sub(r'```\n?', '', query)
        query = query.strip()
        
        if query.upper() == "INVALID_QUESTION":
            return None, {}
        
        # Post-process: Fix "latest" queries that are missing DESC LIMIT 1
        question_lower = question.lower()
        latest_keywords = ["latest", "current", "most recent", "newest", "last"]
        is_latest_question = any(keyword in question_lower for keyword in latest_keywords)
        
        if is_latest_question and "HAS_PRICE" in query.upper():
            # Check if query has ORDER BY but missing DESC LIMIT 1
            if "ORDER BY" in query.upper() and "DESC" not in query.upper():
                # Replace ORDER BY p.date with ORDER BY p.date DESC LIMIT 1
                query = re.sub(r'ORDER BY\s+p\.date\s*$', 'ORDER BY p.date DESC LIMIT 1', query, flags=re.IGNORECASE)
                query = re.sub(r'ORDER BY\s+p\.date\s*\n', 'ORDER BY p.date DESC LIMIT 1\n', query, flags=re.IGNORECASE)
                if "LIMIT 1" not in query.upper():
                    query = query.rstrip() + " DESC LIMIT 1"
                logger.info(f"Fixed 'latest' query to include DESC LIMIT 1")
            elif "ORDER BY" not in query.upper():
                # Add ORDER BY p.date DESC LIMIT 1 if missing
                query = query.rstrip().rstrip(';') + " ORDER BY p.date DESC LIMIT 1"
                logger.info(f"Added ORDER BY p.date DESC LIMIT 1 to 'latest' query")
        
        # Validate query against schema
        is_valid, error_msg = validate_cypher_query(query)
        if not is_valid:
            logger.warning(f"Generated query failed schema validation: {error_msg}")
            logger.warning(f"Query: {query}")
            # Try to fix common issues or return None
            return None, {}
        
        # Extract parameters from the question (use context if available)
        params = extract_query_parameters(question, query, context)
        
        # Cache the query (limit cache size)
        if len(QUERY_CACHE) < 100:  # Limit cache to 100 entries
            QUERY_CACHE[cache_key] = (query, {})
        
        logger.info(f"Generated Cypher query: {query}")
        logger.info(f"Query parameters: {params}")
        
        return query, params
        
    except Exception as e:
        logger.error(f"Error generating Cypher query: {str(e)}")
        return None, {}

def extract_query_parameters(question: str, query: str, context: Optional[dict] = None) -> dict:
    """
    Extract parameters needed for the Cypher query from the question.
    Production-ready with robust extraction and context handling.
    """
    params = {}
    
    # Guard against None query
    if query is None:
        logger.warning("Query is None in extract_query_parameters")
        return params
    
    # Extract symbol if $symbol is in query
    if '$symbol' in query:
        symbol = extract_symbol_from_question(question)
        
        # Use context symbol if question doesn't have one (followup)
        if not symbol and context:
            # Try multiple context sources
            symbol = context.get('last_symbol') or context.get('extracted_symbol')
            if symbol:
                logger.info(f"Using context symbol: {symbol}")
        
        # If still no symbol, try to extract from recent messages
        if not symbol and context and context.get('recent_symbols'):
            recent_symbols = context.get('recent_symbols', [])
            if recent_symbols:
                symbol = recent_symbols[0]  # Use most recent
                logger.info(f"Using recent symbol from context: {symbol}")
        
        if symbol:
            params['symbol'] = symbol
        else:
            query_preview = query[:100] if query else "None"
            logger.warning(f"Could not extract symbol for query: {query_preview}")
    
    # Extract year if $year is in query
    if '$year' in query:
        import re
        year_match = re.search(r'\b(20\d{2})\b', question)
        if year_match:
            params['year'] = int(year_match.group(1))
        elif context and context.get('last_query_type') == 'trend':
            # Use current year as default for trends
            from datetime import datetime
            params['year'] = datetime.now().year
    
    return params

# Pre-compile regex patterns for better performance
SYMBOL_PATTERNS = {
    'dollar': re.compile(r'\$([A-Z]{1,5})\b'),
    'paren': re.compile(r'\(([A-Z]{1,5})\)'),
    'clean': re.compile(r'[^\w\s]')
}

COMMON_WORDS = {
    "WHAT", "IS", "THE", "LATEST", "PRICE", "OF",
    "SHOW", "ME", "TELL", "FOR", "STOCK", "COMPANY",
    "SHARE", "SHARES", "STOCK", "STOCKS", "CURRENT",
    "GET", "GIVE", "FIND", "SEARCH", "LOOKUP"
}

# Company name to ticker symbol mapping
COMPANY_NAME_MAP = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOG",
    "alphabet": "GOOG",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "jpm": "JPM",
    "unitedhealth": "UNH",
    "united health": "UNH",
    "berkshire": "BRK-B",
    "berkshire hathaway": "BRK-B",
    "brk": "BRK-B"
}

# Stock-related keywords that indicate we're talking about stocks, not fruits/other
STOCK_KEYWORDS = {
    "stock", "stocks", "price", "prices", "share", "shares", "ticker", 
    "trading", "market", "company", "companies", "equity", "equities",
    "latest", "current", "close", "open", "high", "low", "volume",
    "performance", "return", "dividend", "earnings", "revenue"
}

def extract_symbol_from_question(question: str) -> Optional[str]:
    """
    Extract stock ticker symbol from question.
    Handles:
    - Direct ticker symbols (AAPL, MSFT)
    - Company names (apple, microsoft)
    - Disambiguation (fruit apple vs Apple company)
    """
    question_lower = question.lower()
    text_upper = question.upper()
    
    # Check if question is about stocks (has stock-related keywords)
    has_stock_context = any(keyword in question_lower for keyword in STOCK_KEYWORDS)
    
    # Try $SYMBOL pattern first
    dollar_match = SYMBOL_PATTERNS['dollar'].search(text_upper)
    if dollar_match:
        symbol = dollar_match.group(1)
        if symbol not in COMMON_WORDS:
            return symbol
    
    # Try (SYMBOL) pattern
    paren_match = SYMBOL_PATTERNS['paren'].search(text_upper)
    if paren_match:
        symbol = paren_match.group(1)
        if symbol not in COMMON_WORDS:
            return symbol
    
    # Check for company names (case-insensitive)
    for company_name, ticker in COMPANY_NAME_MAP.items():
        if company_name in question_lower:
            # Disambiguation: if it's "apple" without stock context, check for fruit indicators
            if company_name == "apple" and not has_stock_context:
                # Check for fruit-related words
                fruit_indicators = ["fruit", "red", "green", "eat", "eating", "taste", "sweet", "tree", "orchard", "juice", "pie", "cider"]
                has_fruit_context = any(indicator in question_lower for indicator in fruit_indicators)
                if has_fruit_context:
                    # This is about fruit, not stock
                    logger.info("Detected fruit context for 'apple', skipping stock symbol extraction")
                    return None
                # If no fruit context, assume it's about the company (this is a stock chatbot)
                logger.info(f"Mapped company name '{company_name}' to ticker '{ticker}' (no fruit context detected)")
                return ticker
            # It's a stock question, return the ticker
            logger.info(f"Mapped company name '{company_name}' to ticker '{ticker}'")
            return ticker
    
    # Extract potential ticker symbols from words
    cleaned = SYMBOL_PATTERNS['clean'].sub(' ', text_upper)
    words = cleaned.split()
    
    candidates = []
    for w in words:
        w_clean = w.strip()
        if w_clean.isalpha() and 1 <= len(w_clean) <= 5:
            if w_clean not in COMMON_WORDS:
                # Check if it's a known ticker symbol
                if w_clean in ["AAPL", "MSFT", "GOOG", "AMZN", "META", "NVDA", "TSLA", "JPM", "UNH", "BRK-B"]:
                    return w_clean
                if 2 <= len(w_clean) <= 5:
                    candidates.insert(0, w_clean)
                else:
                    candidates.append(w_clean)
    
    # If we have stock context and candidates, return the first one
    if has_stock_context and candidates:
        return candidates[0]
    
    # Without stock context, be more conservative
    if candidates and len(candidates[0]) >= 3:  # Prefer longer symbols
        return candidates[0]
    
    return None
