const API_URL = 'http://127.0.0.1:8000/chat';

// Conversation tracking for followups
let conversationId = `conv_${Date.now()}`;
let messageHistory = [];

// Initialize - no persistence, fresh start on every load
document.addEventListener('DOMContentLoaded', () => {
  const questionInput = document.getElementById('questionInput');
  if (questionInput) {
    questionInput.focus();
    
    // Handle Enter key
    questionInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        ask();
      }
    });
  }
});

function addMessage(content, isUser = false, isError = false, metadata = null) {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  
  // Remove welcome message on first user message
  const welcomeMsg = chatMessages.querySelector('.welcome-message');
  if (welcomeMsg && isUser) {
    welcomeMsg.remove();
  }

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
  
  if (isError) {
    messageDiv.classList.add('error');
  }

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.textContent = content;
  bubble.appendChild(contentDiv);
  
  // Add metadata (query trace, confidence) for assistant messages
  if (!isUser && metadata) {
    const metadataDiv = document.createElement('div');
    metadataDiv.className = 'message-metadata';
    
    // Confidence score
    if (metadata.confidence !== undefined) {
      const confidenceDiv = document.createElement('div');
      confidenceDiv.className = 'confidence-score';
      const confidencePercent = Math.round(metadata.confidence * 100);
      confidenceDiv.innerHTML = `<span class="confidence-label">Confidence:</span> <span class="confidence-value">${confidencePercent}%</span>`;
      metadataDiv.appendChild(confidenceDiv);
    }
    
    // Query trace (collapsible)
    if (metadata.generated_query) {
      const queryDiv = document.createElement('details');
      queryDiv.className = 'query-trace';
      const summary = document.createElement('summary');
      summary.textContent = 'View Cypher Query';
      summary.className = 'query-trace-toggle';
      queryDiv.appendChild(summary);
      
      const queryCode = document.createElement('pre');
      queryCode.className = 'query-code';
      queryCode.textContent = metadata.generated_query;
      queryDiv.appendChild(queryCode);
      
      metadataDiv.appendChild(queryDiv);
    }
    
    // Processing time
    if (metadata.processing_time_ms) {
      const timeDiv = document.createElement('div');
      timeDiv.className = 'processing-time';
      timeDiv.textContent = `Processed in ${metadata.processing_time_ms}ms`;
      metadataDiv.appendChild(timeDiv);
    }
    
    if (metadataDiv.children.length > 0) {
      bubble.appendChild(metadataDiv);
    }
  }
  
  messageDiv.appendChild(bubble);
  chatMessages.appendChild(messageDiv);
  
  scrollToBottom();
}

function addTypingIndicator() {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message assistant';
  messageDiv.id = 'typing-indicator';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  
  const typingDiv = document.createElement('div');
  typingDiv.className = 'typing-indicator';
  for (let i = 0; i < 3; i++) {
    const dot = document.createElement('div');
    dot.className = 'typing-dot';
    typingDiv.appendChild(dot);
  }
  bubble.appendChild(typingDiv);
  messageDiv.appendChild(bubble);
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

function removeTypingIndicator() {
  const indicator = document.getElementById('typing-indicator');
  if (indicator) {
    indicator.remove();
  }
}

function scrollToBottom() {
  // Use requestAnimationFrame for better performance
  requestAnimationFrame(() => {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  });
}

function formatResponse(data) {
  // Handle different response types with proper chatbot responses
  if (data.error) {
    switch (data.error) {
      case 'empty_question':
        return "I'm here to help! Please ask me a question about stock prices.";
      
      case 'unsupported_question':
        return "I specialize in stock price information. Try asking something like 'What is the latest price of MSFT?' or 'Show me the price of AAPL'.";
      
      case 'no_symbol_found':
        return "I couldn't identify a stock ticker symbol in your question. Please include a company ticker like MSFT, AAPL, or GOOGL. For example: 'What is the price of MSFT?'";
      
      case 'no_data_found':
        const symbol = data.symbol || 'that symbol';
        return `I couldn't find price data for ${symbol}. The ticker might not be in our database, or it could be misspelled. Could you try a different ticker symbol?`;
      
      case 'database_error':
        return "I'm having trouble accessing the database right now. Please try again in a moment.";
      
      default:
        return "I encountered an issue processing your request. Could you please rephrase your question?";
    }
  }
  
  // Success response
  if (data.answer) {
    return data.answer;
  }
  
  return "I'm not sure how to answer that. Could you ask about a stock price instead?";
}

async function ask() {
  const questionInput = document.getElementById('questionInput');
  const sendButton = document.getElementById('sendButton');
  
  if (!questionInput || !sendButton) return;
  
  const question = questionInput.value.trim();
  
  if (!question) {
    return;
  }

  // Add user message
  addMessage(question, true);
  messageHistory.push({ role: 'user', content: question });

  // Clear input
  questionInput.value = '';
  
  // Disable input while processing
  sendButton.disabled = true;
  questionInput.disabled = true;
  
  // Show typing indicator
  addTypingIndicator();

  try {
    // Add timeout for better UX
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
    
    // Include full conversation history for intelligent context understanding
    const requestBody = {
      question: question,
      conversation_id: conversationId,
      message_history: messageHistory.map(msg => ({
        question: msg.role === 'user' ? msg.content : null,
        answer: msg.role === 'assistant' ? msg.content : null,
        role: msg.role,
        content: msg.content
      })).slice(-10), // Last 10 messages for full context
      context: messageHistory.slice(-10) // Also send as context for backward compatibility
    };
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    removeTypingIndicator();

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const formattedResponse = formatResponse(data);
    
    // Update conversation ID if returned
    if (data.conversation_id) {
      conversationId = data.conversation_id;
    }
    
    // Add assistant response to history
    messageHistory.push({ role: 'assistant', content: formattedResponse });
    
    // Keep history manageable (last 10 messages)
    if (messageHistory.length > 10) {
      messageHistory = messageHistory.slice(-10);
    }
    
    // Determine if it's an error response
    const isError = !!data.error;
    
    // Extract metadata for display
    const metadata = {
      confidence: data.confidence,
      generated_query: data.generated_query,
      processing_time_ms: data.processing_time_ms,
      query_type: data.query_type
    };
    
    addMessage(formattedResponse, false, isError, metadata);

  } catch (error) {
    removeTypingIndicator();
    console.error('Error:', error);
    
    let errorMessage = "I'm having trouble connecting to the server. Please make sure the backend is running.";
    
    if (error.name === 'AbortError') {
      errorMessage = "The request took too long. Please try again with a simpler question.";
    } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      errorMessage = "I can't reach the server right now. Please check that the backend is running on http://127.0.0.1:8000";
    }

    addMessage(errorMessage, false, true);
  } finally {
    const questionInput = document.getElementById('questionInput');
    const sendButton = document.getElementById('sendButton');
    if (questionInput) {
      questionInput.disabled = false;
      questionInput.focus();
    }
    if (sendButton) {
      sendButton.disabled = false;
    }
  }
}

// Fill example question
function fillExample(question) {
  const questionInput = document.getElementById('questionInput');
  if (questionInput) {
    questionInput.value = question;
    questionInput.focus();
    ask();
  }
}

// Export for global access
window.ask = ask;
window.fillExample = fillExample;
