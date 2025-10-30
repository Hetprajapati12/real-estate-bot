"""
Lead detection and buying signal identification.
Analyzes conversation for intent and qualification opportunities.
"""

from typing import List, Dict, Any, Tuple
import re
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def detect_buying_signals(message: str, conversation_history: List[Dict]) -> List[str]:
    """
    Detect buying signals in user message.
    
    Args:
        message: User's message
        conversation_history: Previous conversation messages
        
    Returns:
        List of detected buying signals
    """
    signals = []
    message_lower = message.lower()
    
    # Budget mentions
    if detect_budget_mention(message_lower):
        signals.append("budget_mentioned")
    
    # Specific requirements
    if detect_specific_requirements(message_lower):
        signals.append("specific_requirements")
    
    # Timeline indicators
    if detect_timeline(message_lower):
        signals.append("timeline_mentioned")
    
    # Location preferences
    if detect_location_preference(message_lower):
        signals.append("location_preference")
    
    # Luxury features interest
    if detect_luxury_interest(message_lower):
        signals.append("luxury_feature_interest")
    
    # Comparison behavior
    if detect_comparison_intent(message_lower):
        signals.append("comparison_intent")
    
    # Purchase process questions
    if detect_purchase_questions(message_lower):
        signals.append("purchase_process_inquiry")
    
    # Viewing/visit interest
    if detect_viewing_interest(message_lower):
        signals.append("viewing_interest")
    
    # Current situation
    if detect_current_situation(message_lower):
        signals.append("current_situation_shared")
    
    logger.debug(f"Detected signals: {signals}")
    return signals


def detect_budget_mention(text: str) -> bool:
    """Check for budget-related keywords."""
    budget_keywords = [
        r'\$[\d,]+', r'aed[\s]?[\d,]+', r'budget', r'price', r'cost',
        r'afford', r'million', r'thousand', r'payment', r'financing'
    ]
    return any(re.search(pattern, text) for pattern in budget_keywords)


def detect_specific_requirements(text: str) -> bool:
    """Check for specific property requirements."""
    requirement_keywords = [
        r'\d+\s*bedroom', r'\d+br', r'pool', r'garden', r'parking',
        r'sqm', r'square', r'layout', r'master bedroom', r'ensuite',
        r'maid room', r'storage', r'terrace', r'balcony'
    ]
    return any(re.search(pattern, text) for pattern in requirement_keywords)


def detect_timeline(text: str) -> bool:
    """Check for timeline indicators."""
    timeline_keywords = [
        r'soon', r'urgently', r'asap', r'immediately', r'next month',
        r'by\s+\w+', r'looking to move', r'need by', r'within',
        r'this year', r'next year', r'\d+\s*months?'
    ]
    return any(re.search(pattern, text) for pattern in timeline_keywords)


def detect_location_preference(text: str) -> bool:
    """Check for location preferences."""
    location_keywords = [
        r'dubai', r'festival city', r'al badia', r'area', r'location',
        r'neighborhood', r'near', r'close to', r'proximity'
    ]
    return any(re.search(pattern, text) for pattern in location_keywords)


def detect_luxury_interest(text: str) -> bool:
    """Check for luxury feature interest."""
    luxury_keywords = [
        r'luxury', r'premium', r'high-end', r'upscale', r'exclusive',
        r'pool', r'golf', r'spa', r'gym', r'clubhouse'
    ]
    return any(re.search(pattern, text) for pattern in luxury_keywords)


def detect_comparison_intent(text: str) -> bool:
    """Check for comparison behavior."""
    comparison_keywords = [
        r'compare', r'versus', r'vs', r'difference', r'better',
        r'which one', r'or', r'between'
    ]
    return any(re.search(pattern, text) for pattern in comparison_keywords)


def detect_purchase_questions(text: str) -> bool:
    """Check for purchase process questions."""
    purchase_keywords = [
        r'how to buy', r'purchase', r'documentation', r'paperwork',
        r'mortgage', r'loan', r'financing', r'down payment',
        r'process', r'steps', r'requirements'
    ]
    return any(re.search(pattern, text) for pattern in purchase_keywords)


def detect_viewing_interest(text: str) -> bool:
    """Check for viewing/visit interest."""
    viewing_keywords = [
        r'visit', r'view', r'see', r'tour', r'show', r'schedule',
        r'appointment', r'when can', r'available to see'
    ]
    return any(re.search(pattern, text) for pattern in viewing_keywords)


def detect_current_situation(text: str) -> bool:
    """Check if user shared current living situation."""
    situation_keywords = [
        r'currently', r'renting', r'selling', r'own', r'living in',
        r'lease', r'tenant', r'landlord', r'moving from'
    ]
    return any(re.search(pattern, text) for pattern in situation_keywords)


def calculate_intent_score(signals: List[str], conversation_length: int) -> float:
    """
    Calculate overall intent score based on signals.
    
    Args:
        signals: List of detected buying signals
        conversation_length: Number of messages in conversation
        
    Returns:
        Intent score between 0 and 1
    """
    # Base score from signals
    signal_weights = {
        "budget_mentioned": 0.15,
        "specific_requirements": 0.12,
        "timeline_mentioned": 0.15,
        "location_preference": 0.08,
        "luxury_feature_interest": 0.08,
        "comparison_intent": 0.10,
        "purchase_process_inquiry": 0.15,
        "viewing_interest": 0.20,
        "current_situation_shared": 0.10
    }
    
    base_score = sum(signal_weights.get(signal, 0.05) for signal in signals)
    
    # Bonus for conversation engagement
    engagement_bonus = min(conversation_length * 0.02, 0.15)
    
    # Total score capped at 1.0
    total_score = min(base_score + engagement_bonus, 1.0)
    
    return total_score


def classify_intent(intent_score: float) -> str:
    """
    Classify intent level based on score.
    
    Args:
        intent_score: Calculated intent score
        
    Returns:
        Intent classification (low/medium/high)
    """
    if intent_score >= settings.INTENT_HIGH_THRESHOLD:
        return "high"
    elif intent_score >= settings.INTENT_MEDIUM_THRESHOLD:
        return "medium"
    else:
        return "low"


def recommend_action(intent_level: str, signals: List[str]) -> str:
    """
    Recommend next action based on intent and signals.
    
    Args:
        intent_level: Intent classification
        signals: Detected buying signals
        
    Returns:
        Recommended action
    """
    if intent_level == "high":
        if "viewing_interest" in signals:
            return "schedule_viewing_immediately"
        return "capture_contact_and_schedule_callback"
    
    elif intent_level == "medium":
        if "specific_requirements" in signals:
            return "show_floorplans_and_qualify"
        if "comparison_intent" in signals:
            return "provide_comparison_capture_preference"
        return "share_more_details_build_interest"
    
    else:  # low intent
        return "educate_and_build_interest"


def extract_contact_info(message: str) -> Dict[str, str]:
    """
    Extract contact information from message.
    
    Args:
        message: User message
        
    Returns:
        Dictionary with extracted contact details
    """
    contact_info = {}
    
    # Email regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, message)
    if emails:
        contact_info["email"] = emails[0]
    
    # Phone regex (various formats)
    phone_patterns = [
        r'\+971[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}',  # UAE format
        r'\+\d{1,3}[\s-]?\d{3,4}[\s-]?\d{3,4}[\s-]?\d{3,4}',  # International
        r'\d{3}[\s-]?\d{3}[\s-]?\d{4}',  # Standard format
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, message)
        if phones:
            contact_info["phone"] = phones[0]
            break
    
    # Name extraction (if introduced as "I'm [Name]" or "My name is [Name]")
    name_patterns = [
        r"(?:i'm|i am|my name is|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:call me|contact)\s+([A-Z][a-z]+)"
    ]
    for pattern in name_patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        if matches:
            contact_info["name"] = matches[0]
            break
    
    return contact_info


def generate_lead_signals_response(
    signals: List[str],
    intent_score: float,
    conversation_history: List[Dict]
) -> Dict[str, Any]:
    """
    Generate complete lead signals response.
    
    Args:
        signals: Detected buying signals
        intent_score: Calculated intent score
        conversation_history: Conversation messages
        
    Returns:
        Lead signals dictionary
    """
    intent_level = classify_intent(intent_score)
    action = recommend_action(intent_level, signals)
    
    return {
        "intent": intent_level,
        "intent_score": round(intent_score, 2),
        "signals_detected": signals,
        "recommended_action": action,
        "conversation_depth": len(conversation_history)
    }


def should_request_contact_info(
    lead_info: Dict[str, str],
    intent_level: str,
    conversation_length: int
) -> Tuple[bool, str]:
    """
    Determine if and what contact info to request.
    
    Args:
        lead_info: Currently captured lead information
        intent_level: Calculated intent level
        conversation_length: Number of messages
        
    Returns:
        Tuple of (should_request, what_to_request)
    """
    # Don't be too pushy early in conversation
    if conversation_length < 2:
        return False, ""
    
    # High intent - try to get any missing info
    if intent_level == "high":
        if not lead_info.get("phone") and not lead_info.get("email"):
            return True, "contact_method"
        elif not lead_info.get("name"):
            return True, "name"
    
    # Medium intent - gently suggest contact
    elif intent_level == "medium" and conversation_length >= 3:
        if not lead_info.get("email"):
            return True, "email_for_brochure"
    
    return False, ""