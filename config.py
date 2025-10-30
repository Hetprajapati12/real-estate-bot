"""
Configuration management for the Real Estate RAG Chatbot.
Loads settings from environment variables with validation.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent


def create_required_directories(config: 'Settings') -> None:
    """Create required directories if they don't exist."""
    Path(config.CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)
    Path(config.IMAGES_DIR).mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="Anthropic API key (optional)")
    
    # Vector Database
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./data/chroma_db",
        description="ChromaDB persistence directory"
    )
    
    # Application
    APP_HOST: str = Field(default="0.0.0.0", description="Application host")
    APP_PORT: int = Field(default=8000, description="Application port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Data Paths
    PDF_PATH: str = Field(
        default="./data/ABVFinalFloorplans.pdf",
        description="Path to floorplans PDF"
    )
    IMAGES_DIR: str = Field(
        default="./data/WebP",
        description="Directory containing floorplan images"
    )
    
    # LLM Configuration
    LLM_MODEL: str = Field(default="gpt-4-turbo-preview", description="LLM model name")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Embedding model")
    TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    MAX_TOKENS: int = Field(default=1000, gt=0, description="Maximum response tokens")
    
    # RAG Configuration
    CHUNK_SIZE: int = Field(default=1000, gt=0, description="Text chunk size for embeddings")
    CHUNK_OVERLAP: int = Field(default=200, ge=0, description="Overlap between chunks")
    TOP_K_RESULTS: int = Field(default=5, gt=0, description="Number of retrieval results")
    SIMILARITY_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score"
    )
    
    # Lead Scoring
    INTENT_LOW_THRESHOLD: float = Field(default=0.3, ge=0.0, le=1.0)
    INTENT_MEDIUM_THRESHOLD: float = Field(default=0.6, ge=0.0, le=1.0)
    INTENT_HIGH_THRESHOLD: float = Field(default=0.8, ge=0.0, le=1.0)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


def load_settings() -> Settings:
    """Load and validate application settings."""
    settings = Settings()
    create_required_directories(settings)
    return settings


# Global settings instance
settings = load_settings()