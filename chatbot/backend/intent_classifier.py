"""
Intent Classification Module
Distinguishes between conversational questions and data queries
"""
from openai import OpenAI
import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Initialize client
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key, timeout=10.0)
else:
    client = None

def classify_intent(question: str, context: Optional[dict] = None) -> Tuple[str, dict]:
    """
    Classify the intent of a question.
    Returns: (intent_type, intent_data)
    
    Intent types:
    - "data_query": Needs Cypher query generation
    - "conversational": Can be answered directly without query
    - "clarification": Asking about previous answer
    - "confirmation": Asking for confirmation
    """
    if not client:
        # Fallback: assume data query if no LLM
        return "data_query", {}
    
    # Quick pattern matching for common conversational intents
    question_lower = question.lower().strip()
    
    # Data query indicators (must be data queries, not conversational)
    data_query_indicators = [
        "price", "stock", "share", "ticker", "company", "trading", "volume",
        "outperform", "compare", "trend", "correlat", "similar", "influential",
        "pagerank", "community", "group", "vs", "versus", "better", "worse",
        "what is", "what are", "which", "show me", "tell me", "give me",
        "how did", "how much", "when", "where"
    ]
    
    # If question contains data query indicators, it's definitely a data query
    if any(indicator in question_lower for indicator in data_query_indicators):
        return "data_query", {}
    
    # Conversational patterns (only if no data query indicators)
    conversational_patterns = [
        "are you sure", "are u sure", "really", "seriously",
        "thanks", "thank you", "thank", "thx",
        "ok", "okay", "got it", "understood",
        "what do you mean", "what does that mean", "explain",
        "can you repeat", "say that again", "what was that",
        "yes", "no", "correct", "right", "wrong",
        "hello", "hi", "hey", "greetings"
    ]
    
    for pattern in conversational_patterns:
        if pattern in question_lower:
            if any(p in question_lower for p in ["sure", "really", "seriously"]):
                return "confirmation", {"type": "confirmation"}
            elif any(p in question_lower for p in ["mean", "explain", "repeat"]):
                return "clarification", {"type": "clarification"}
            else:
                return "conversational", {"type": "greeting" if any(p in question_lower for p in ["hello", "hi", "hey"]) else "general"}
    
    # Use LLM for ambiguous cases
    try:
        prompt = f"""Classify this question as one of:
- "data_query": Needs database query (e.g., "What is the price of MSFT?")
- "conversational": General chat (e.g., "thanks", "are you sure")
- "clarification": Asking about previous answer (e.g., "what do you mean?")
- "confirmation": Asking for confirmation (e.g., "are you sure?")

Question: {question}
Context: {context.get('last_answer', 'No previous answer') if context else 'No context'}

Respond with ONLY the intent type (data_query, conversational, clarification, or confirmation):"""
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=20,
            timeout=5.0
        )
        
        intent = resp.choices[0].message.content.strip().lower()
        
        # Validate intent
        valid_intents = ["data_query", "conversational", "clarification", "confirmation"]
        if intent not in valid_intents:
            # Default to data_query if unclear
            logger.warning(f"Unclear intent '{intent}', defaulting to data_query")
            return "data_query", {}
        
        intent_data = {"type": intent}
        
        # Add context for clarification/confirmation
        if intent in ["clarification", "confirmation"] and context:
            intent_data["last_answer"] = context.get("last_answer", "")
            intent_data["last_symbol"] = context.get("last_symbol", "")
        
        return intent, intent_data
        
    except Exception as e:
        logger.error(f"Error classifying intent: {str(e)}")
        # Default to data_query on error
        return "data_query", {}

def handle_conversational_intent(question: str, intent_data: dict, context: Optional[dict] = None) -> str:
    """
    Handle conversational intents without database queries.
    """
    question_lower = question.lower().strip()
    
    # Confirmation requests
    if intent_data.get("type") == "confirmation" and context:
        last_answer = context.get("last_answer", "")
        if last_answer:
            return f"Yes, I'm confident about that. {last_answer}"
        return "Yes, I'm sure about the information I provided."
    
    # Clarification requests
    if intent_data.get("type") == "clarification" and context:
        last_answer = context.get("last_answer", "")
        if last_answer:
            return f"Let me clarify: {last_answer} In simpler terms, this is the most recent stock price data I found in the database."
        return "I'd be happy to clarify. Could you be more specific about what you'd like me to explain?"
    
    # Greetings
    if any(word in question_lower for word in ["hello", "hi", "hey", "greetings"]):
        return "Hello! I can help you find stock prices. Ask me about any company ticker symbol."
    
    # Thanks
    if any(word in question_lower for word in ["thanks", "thank you", "thank", "thx"]):
        return "You're welcome! Feel free to ask if you need any other stock information."
    
    # General conversational
    if any(word in question_lower for word in ["ok", "okay", "got it", "understood"]):
        return "Great! Is there anything else you'd like to know about stock prices?"
    
    # Check if it might be a stock question but symbol extraction failed
    question_lower = question.lower()
    stock_indicators = ["price", "stock", "share", "ticker", "company", "trading"]
    if any(word in question_lower for word in stock_indicators):
        return "I'm here to help with stock price information. Please specify a company name or ticker symbol (e.g., 'Apple', 'AAPL', 'Microsoft', 'MSFT')."
    
    # Default conversational response
    return "I'm here to help with stock price information. Could you ask me a specific question about stock prices?"

