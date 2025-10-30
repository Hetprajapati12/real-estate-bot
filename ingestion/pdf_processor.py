"""
PDF processing and text extraction.
Handles Al Badia Villas floorplans PDF with page-level metadata.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_pdf_pages(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from PDF with page-level metadata.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing page text and metadata
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF cannot be processed
    """
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    logger.info(f"Processing PDF: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        pages_data = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            
            # Skip empty pages
            if not text.strip():
                logger.debug(f"Skipping empty page {page_num + 1}")
                continue
            
            page_data = {
                "page_number": page_num + 1,
                "text": text,
                "metadata": {
                    "source": pdf_file.name,
                    "page": page_num + 1,
                    "total_pages": len(doc),
                    "source_type": "floorplans_pdf"
                }
            }
            
            pages_data.append(page_data)
            logger.debug(f"Extracted page {page_num + 1}: {len(text)} characters")
        
        doc.close()
        logger.info(f"Successfully extracted {len(pages_data)} pages from PDF")
        
        return pages_data
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise ValueError(f"Failed to process PDF: {str(e)}")


def identify_villa_pages(pages_data: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """
    Identify which pages contain specific villa types.
    Based on Al Badia Villas structure.
    
    Args:
        pages_data: List of page data dictionaries
        
    Returns:
        Dictionary mapping villa types to page numbers
    """
    villa_pages = {
        "3BR_MIA_TYPE_A": [],
        "3BR_MIA_TYPE_B": [],
        "4BR_SHADEA_TYPE_A": [],
        "4BR_SHADEA_TYPE_B": [],
        "5BR_MODEA_TYPE_A": [],
        "5BR_MODEA_TYPE_B": [],
    }
    
    # Keywords to identify villa types
    keywords = {
        "3BR_MIA_TYPE_A": ["3BR", "MIA", "TYPE A", "3 BEDROOM"],
        "3BR_MIA_TYPE_B": ["3BR", "MIA", "TYPE B", "3 BEDROOM", "POOL"],
        "4BR_SHADEA_TYPE_A": ["4BR", "SHADEA", "TYPE A", "4 BEDROOM"],
        "4BR_SHADEA_TYPE_B": ["4BR", "SHADEA", "TYPE B", "4 BEDROOM", "POOL"],
        "5BR_MODEA_TYPE_A": ["5BR", "MODEA", "TYPE A", "5 BEDROOM"],
        "5BR_MODEA_TYPE_B": ["5BR", "MODEA", "TYPE B", "5 BEDROOM", "POOL"],
    }
    
    for page_data in pages_data:
        text_upper = page_data["text"].upper()
        page_num = page_data["page_number"]
        
        for villa_type, terms in keywords.items():
            # Check if multiple keywords match
            matches = sum(1 for term in terms if term in text_upper)
            if matches >= 2:  # At least 2 keywords must match
                villa_pages[villa_type].append(page_num)
                logger.debug(f"Page {page_num} identified as {villa_type}")
    
    return villa_pages


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            last_period = text.rfind('.', start, end)
            last_newline = text.rfind('\n', start, end)
            break_point = max(last_period, last_newline)
            
            if break_point > start:
                end = break_point + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks


def create_chunks_with_metadata(
    pages_data: List[Dict[str, Any]],
    chunk_size: int,
    overlap: int
) -> List[Dict[str, Any]]:
    """
    Create text chunks with preserved metadata.
    
    Args:
        pages_data: List of page data dictionaries
        chunk_size: Chunk size in characters
        overlap: Overlap between chunks
        
    Returns:
        List of chunk dictionaries with metadata
    """
    all_chunks = []
    
    for page_data in pages_data:
        text = page_data["text"]
        chunks = chunk_text(text, chunk_size, overlap)
        
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "text": chunk,
                "metadata": {
                    **page_data["metadata"],
                    "chunk_id": f"page_{page_data['page_number']}_chunk_{i}",
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }
            all_chunks.append(chunk_data)
    
    logger.info(f"Created {len(all_chunks)} chunks from {len(pages_data)} pages")
    return all_chunks