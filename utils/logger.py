"""
Logging configuration using loguru.
Provides structured logging with proper formatting.
"""

import sys
from loguru import logger
from config import settings


def setup_logger() -> None:
    """Configure logger with appropriate settings."""
    logger.remove()
    
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="00:00",
        retention="30 days",
        compression="zip",
    )


def get_logger(name: str):
    """Get a logger instance with the specified name."""
    return logger.bind(name=name)


# Initialize logger on import
setup_logger()