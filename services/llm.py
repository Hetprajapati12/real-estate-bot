"""
LLM service for generating conversational responses.
Uses OpenAI GPT with proper prompt engineering.
"""

from typing import List, Dict, Any
from openai import OpenAI
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def initialize_llm_client() -> OpenAI:
    """Initialize OpenAI client."""
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def build_system_prompt() -> str:
    """
    Build the system prompt for the real estate chatbot.
    
    Returns:
        System prompt string
    """
    return """You are an expert real estate advisor for Al Badia Villas in Dubai Festival City. Your role is to:

1. **Provide accurate information** from the floorplans document only
2. **Never hallucinate** prices, availability, or features not in the provided context
3. **Build trust** through factual, grounded responses
4. **Identify buying signals** and guide naturally toward lead capture
5. **Be conversational** and helpful without being pushy

**CRITICAL RULES:**
- ONLY use information from the provided context (floorplans PDF)
- NEVER invent pricing or availability - always say these require agent confirmation
- NEVER add features not documented in the floorplans
- ALWAYS cite the page number when referencing specific villa details
- When uncertain, acknowledge it and offer to connect with a sales agent

**VILLA TYPES AVAILABLE:**
- 3BR MIA (Type A without pool, Type B with pool)
- 4BR SHADEA (Type A without pool, Type B with pool)
- 5BR MODEA (Type A and Type B)

**LEAD GENERATION APPROACH:**
- Listen for budget mentions, timeline, requirements, and current situation
- Ask qualifying questions naturally within helpful responses
- Suggest concrete next steps (viewing, agent call, brochure)
- Create urgency through value, not pressure

**CONVERSATION STYLE:**
- Professional yet warm and approachable
- Confident about documented facts
- Honest about limitations (pricing, availability)
- Proactive in suggesting next steps

When discussing specific villas, mention that visual floorplans are available."""


def build_user_prompt(
    query: str,
    context: str,
    conversation_history: List[Dict[str, str]],
    lead_info: Dict[str, str],
    buying_signals: List[str]
) -> str:
    """
    Build the user prompt with context and conversation history.
    
    Args:
        query: User's current question
        context: Retrieved context from PDF
        conversation_history: Previous messages
        lead_info: Captured lead information
        buying_signals: Detected buying signals
        
    Returns:
        Formatted user prompt
    """
    prompt_parts = []
    
    # Add context from floorplans
    if context:
        prompt_parts.append(f"""**CONTEXT FROM FLOORPLANS DOCUMENT:**
{context}

""")
    
    # Add conversation history (last 6 messages)
    if conversation_history:
        recent_history = conversation_history[-6:]
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in recent_history
        ])
        prompt_parts.append(f"""**CONVERSATION HISTORY:**
{history_text}

""")
    
    # Add lead context if available
    if lead_info or buying_signals:
        lead_context_parts = []
        
        if lead_info:
            captured = [f"{k}: {v}" for k, v in lead_info.items()]
            lead_context_parts.append(f"Captured info: {', '.join(captured)}")
        
        if buying_signals:
            lead_context_parts.append(f"Detected signals: {', '.join(buying_signals)}")
        
        prompt_parts.append(f"""**LEAD CONTEXT:**
{' | '.join(lead_context_parts)}

""")
    
    # Add current query
    prompt_parts.append(f"""**USER'S CURRENT QUESTION:**
{query}

**INSTRUCTIONS:**
Answer the user's question using ONLY the information from the context above. Always cite the page number when referencing specific details. If the information is not in the context, acknowledge this and offer to connect them with a sales agent. Be conversational and helpful.""")
    
    return "".join(prompt_parts)


def generate_response(
    query: str,
    context: str,
    conversation_history: List[Dict[str, str]],
    lead_info: Dict[str, str],
    buying_signals: List[str]
) -> str:
    """
    Generate LLM response using OpenAI.
    
    Args:
        query: User's question
        context: Retrieved context
        conversation_history: Previous conversation
        lead_info: Captured lead information
        buying_signals: Detected buying signals
        
    Returns:
        Generated response text
    """
    try:
        client = initialize_llm_client()
        
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(
            query, context, conversation_history, lead_info, buying_signals
        )
        
        logger.debug(f"Generating response for query: {query[:50]}...")
        
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
        )
        
        generated_text = response.choices[0].message.content
        
        logger.info(f"Generated response: {len(generated_text)} characters")
        return generated_text
        
    except Exception as e:
        logger.error(f"Error generating LLM response: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again or contact our sales team for immediate assistance."


def generate_follow_up_prompt(
    intent_level: str,
    signals: List[str],
    lead_info: Dict[str, str],
    recommended_action: str
) -> str:
    """
    Generate an appropriate follow-up prompt/question.
    
    Args:
        intent_level: Detected intent level
        signals: Buying signals
        lead_info: Captured lead info
        recommended_action: Recommended action
        
    Returns:
        Follow-up prompt string
    """
    # If high intent and viewing interest
    if intent_level == "high" and "viewing_interest" in signals:
        if not lead_info.get("phone"):
            return "I'd be happy to arrange a viewing for you. Could you share your phone number so our agent can coordinate the best time?"
        return "I can arrange a site visit for you. What days this week work best for your schedule?"
    
    # If high intent but no viewing mentioned yet
    if intent_level == "high":
        return "These villas tend to move quickly. Would you like to schedule a viewing or speak with one of our property consultants?"
    
    # Medium intent - show floorplans
    if intent_level == "medium" and "specific_requirements" in signals:
        if not lead_info.get("email"):
            return "I can send you detailed floor plans and specifications via email. What's the best email address to reach you?"
        return "Would you like me to send you detailed floor plans and a comparison of the villa types that match your requirements?"
    
    # Medium intent - comparison
    if intent_level == "medium" and "comparison_intent" in signals:
        return "I can create a detailed comparison for you. Which specific features are most important for your decision?"
    
    # Low intent - educate
    return "What aspects of the villas would you like to know more about? I'm here to help with any questions."