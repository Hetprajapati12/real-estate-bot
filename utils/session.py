"""
Session management for conversation continuity.
Stores conversation history and context per session.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

# In-memory session store (use Redis in production)
_sessions: Dict[str, Dict[str, Any]] = {}

# Session expiry time
SESSION_EXPIRY_HOURS = 24


def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get or create a session by ID.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Session data dictionary
    """
    if session_id not in _sessions:
        _sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": [],
            "properties_viewed": [],
            "lead_info": {},
            "lead_status": "new",
            "buying_signals": [],
        }
        logger.info(f"Created new session: {session_id}")
    else:
        # Update last accessed time
        _sessions[session_id]["updated_at"] = datetime.now()
    
    return _sessions[session_id]


def update_session(session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update session data.
    
    Args:
        session_id: Session identifier
        updates: Dictionary of fields to update
        
    Returns:
        Updated session data
    """
    session = get_session(session_id)
    session.update(updates)
    session["updated_at"] = datetime.now()
    
    logger.debug(f"Updated session {session_id}: {list(updates.keys())}")
    return session


def add_message(session_id: str, role: str, content: str) -> None:
    """
    Add a message to session history.
    
    Args:
        session_id: Session identifier
        role: Message role (user/assistant)
        content: Message content
    """
    session = get_session(session_id)
    session["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    session["updated_at"] = datetime.now()


def add_property_viewed(session_id: str, property_id: str) -> None:
    """
    Track property viewing in session.
    
    Args:
        session_id: Session identifier
        property_id: Property/villa identifier
    """
    session = get_session(session_id)
    if property_id not in session["properties_viewed"]:
        session["properties_viewed"].append(property_id)
        logger.info(f"Session {session_id} viewed property: {property_id}")


def add_buying_signal(session_id: str, signal: str) -> None:
    """
    Record a buying signal detected in conversation.
    
    Args:
        session_id: Session identifier
        signal: Description of the buying signal
    """
    session = get_session(session_id)
    if signal not in session["buying_signals"]:
        session["buying_signals"].append(signal)
        logger.info(f"Detected buying signal in {session_id}: {signal}")


def update_lead_status(session_id: str, status: str) -> None:
    """
    Update lead qualification status.
    
    Args:
        session_id: Session identifier
        status: Lead status (new/qualified/hot/converted)
    """
    session = get_session(session_id)
    session["lead_status"] = status
    logger.info(f"Updated lead status for {session_id}: {status}")


def get_conversation_history(session_id: str, last_n: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
        last_n: Optional limit to last N messages
        
    Returns:
        List of message dictionaries
    """
    session = get_session(session_id)
    messages = session["messages"]
    
    if last_n is not None and last_n > 0:
        return messages[-last_n:]
    
    return messages


def cleanup_expired_sessions() -> int:
    """
    Remove sessions older than expiry time.
    
    Returns:
        Number of sessions cleaned up
    """
    expiry_time = datetime.now() - timedelta(hours=SESSION_EXPIRY_HOURS)
    expired_sessions = [
        sid for sid, session in _sessions.items()
        if session["updated_at"] < expiry_time
    ]
    
    for session_id in expired_sessions:
        del _sessions[session_id]
    
    if expired_sessions:
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    return len(expired_sessions)