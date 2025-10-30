"""
FastAPI application for Real Estate RAG Chatbot.
Provides /chat endpoint for conversational interactions.
"""

from fastapi import FastAPI, HTTPException, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import uvicorn

from dotenv import load_dotenv
load_dotenv()


from config import settings
from retrieval.vector_store import initialize_vector_store
from services.chat import process_chat_message, validate_chat_request
from utils.session import cleanup_expired_sessions
from utils.logger import get_logger

logger = get_logger(__name__)

# Global vector store instance
vectorstore = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    global vectorstore
    logger.info("Starting application...")
    
    try:
        vectorstore = initialize_vector_store()
        logger.info("Vector store loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
        raise RuntimeError(
            "Vector store not found. Please run 'python ingest_data.py' first."
        )
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    cleanup_expired_sessions()


# Initialize FastAPI app
app = FastAPI(
    title="Real Estate RAG Chatbot",
    description="AI-powered chatbot for Al Badia Villas with RAG and lead generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatContext(BaseModel):
    """Optional context for the chat request."""
    previous_properties_viewed: Optional[List[str]] = Field(default_factory=list)
    lead_status: Optional[str] = "new"


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User's message", min_length=1)
    session_id: str = Field(..., description="Unique session identifier")
    context: Optional[ChatContext] = Field(default_factory=ChatContext)


class ImageInfo(BaseModel):
    """Image information model."""
    path: str
    description: str
    relevance: str


class CitationInfo(BaseModel):
    """Citation information model."""
    source: str
    page: int
    villa_type: str


class LeadSignals(BaseModel):
    """Lead signals information."""
    intent: str
    intent_score: Optional[float] = None
    signals_detected: List[str]
    recommended_action: str
    conversation_depth: Optional[int] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    properties_mentioned: List[str]
    citations: List[CitationInfo]
    images: List[ImageInfo]
    lead_signals: LeadSignals
    follow_up_prompt: str


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again."
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "vectorstore_loaded": vectorstore is not None
    }


# Main chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return AI response with lead insights.
    
    Args:
        request: Chat request containing message and session info
        
    Returns:
        ChatResponse with AI reply, images, citations, and lead signals
        
    Raises:
        HTTPException: If request validation fails or processing errors occur
    """
    logger.info(f"Received chat request for session: {request.session_id}")
    
    # Validate request
    is_valid, error_msg = validate_chat_request(request.dict())
    if not is_valid:
        logger.warning(f"Invalid request: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check vector store
    if vectorstore is None:
        logger.error("Vector store not initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Please ensure data ingestion has been completed."
        )
    
    try:
        # Process the message
        response = process_chat_message(
            message=request.message,
            session_id=request.session_id,
            context=request.context.dict() if request.context else {},
            vectorstore=vectorstore
        )
        
        logger.info(f"Successfully processed message for session: {request.session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process your message. Please try again."
        )


# Session cleanup endpoint (optional, for admin use)
@app.post("/admin/cleanup-sessions")
async def cleanup_sessions_endpoint():
    """
    Cleanup expired sessions (admin endpoint).
    
    Returns:
        Number of sessions cleaned up
    """
    count = cleanup_expired_sessions()
    return {"cleaned_up": count, "message": f"Cleaned up {count} expired sessions"}


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        API information
    """
    return {
        "name": "Real Estate RAG Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "docs": "/docs"
        }
    }


def run_server():
    """Run the FastAPI server."""
    logger.info(f"Starting server on {settings.APP_HOST}:{settings.APP_PORT}")
    
    uvicorn.run(
        "app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    run_server()