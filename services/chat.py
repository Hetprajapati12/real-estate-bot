"""
Chat service that orchestrates the complete conversation flow.
Handles retrieval, generation, lead detection, and response formatting.
"""

from typing import Dict, Any
from retrieval.rag import (
    retrieve_context,
    format_context_for_prompt,
    extract_citations,
    identify_mentioned_properties,
    should_include_images,
    rank_images_by_relevance
)
from lead.detector import (
    detect_buying_signals,
    calculate_intent_score,
    generate_lead_signals_response,
    extract_contact_info,
    should_request_contact_info
)
from services.llm import generate_response, generate_follow_up_prompt
from utils.session import (
    get_session,
    update_session,
    add_message,
    add_property_viewed,
    add_buying_signal,
    get_conversation_history
)
from utils.logger import get_logger

logger = get_logger(__name__)


def process_chat_message(
    message: str,
    session_id: str,
    context: Dict[str, Any],
    vectorstore
) -> Dict[str, Any]:
    """
    Process a chat message and generate a complete response.
    
    Args:
        message: User's message
        session_id: Session identifier
        context: Additional context from request
        vectorstore: Vector store instance
        
    Returns:
        Complete response dictionary
    """
    logger.info(f"Processing message for session {session_id}")
    
    # Get session data
    session = get_session(session_id)
    
    # Add user message to history
    add_message(session_id, "user", message)
    
    # Extract any contact info from message
    new_contact_info = extract_contact_info(message)
    if new_contact_info:
        session["lead_info"].update(new_contact_info)
        logger.info(f"Captured contact info: {list(new_contact_info.keys())}")
    
    # Get conversation history
    conversation_history = get_conversation_history(session_id)
    
    # Detect buying signals
    buying_signals = detect_buying_signals(message, conversation_history)
    
    # Update session with new signals
    for signal in buying_signals:
        add_buying_signal(session_id, signal)
    
    # Calculate intent score
    all_signals = session.get("buying_signals", [])
    intent_score = calculate_intent_score(all_signals, len(conversation_history))
    
    # Generate lead signals response
    lead_signals = generate_lead_signals_response(
        all_signals, intent_score, conversation_history
    )
    
    # Retrieve relevant context
    pdf_results, image_results = retrieve_context(vectorstore, message)
    
    # Format context for LLM
    formatted_context = format_context_for_prompt(pdf_results)
    
    # Generate response
    response_text = generate_response(
        query=message,
        context=formatted_context,
        conversation_history=conversation_history[:-1],  # Exclude current message
        lead_info=session.get("lead_info", {}),
        buying_signals=all_signals
    )
    
    # Add assistant response to history
    add_message(session_id, "assistant", response_text)
    
    # Identify mentioned properties
    mentioned_properties = identify_mentioned_properties(response_text)
    
    # Track viewed properties
    for prop in mentioned_properties:
        add_property_viewed(session_id, prop)
    
    # Extract citations
    citations = extract_citations(pdf_results)
    
    # Determine if images should be included
    include_images = should_include_images(message) or len(mentioned_properties) > 0
    
    # Rank and filter images
    relevant_images = []
    if include_images and image_results:
        ranked_images = rank_images_by_relevance(image_results, message, pdf_results)
        # Take top 3 most relevant
        relevant_images = ranked_images[:3]
    
    # Generate follow-up prompt
    follow_up = generate_follow_up_prompt(
        intent_level=lead_signals["intent"],
        signals=all_signals,
        lead_info=session.get("lead_info", {}),
        recommended_action=lead_signals["recommended_action"]
    )
    
    # Build complete response
    response = {
        "response": response_text,
        "properties_mentioned": mentioned_properties,
        "citations": citations,
        "images": relevant_images,
        "lead_signals": lead_signals,
        "follow_up_prompt": follow_up
    }
    
    logger.info(
        f"Response generated: {len(response_text)} chars, "
        f"{len(mentioned_properties)} properties, "
        f"{len(relevant_images)} images"
    )
    
    return response


def validate_chat_request(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate incoming chat request.
    
    Args:
        data: Request data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data.get("message"):
        return False, "Message is required"
    
    if not isinstance(data["message"], str):
        return False, "Message must be a string"
    
    if len(data["message"].strip()) == 0:
        return False, "Message cannot be empty"
    
    if not data.get("session_id"):
        return False, "Session ID is required"
    
    return True, ""