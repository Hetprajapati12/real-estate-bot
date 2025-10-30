"""
RAG (Retrieval-Augmented Generation) implementation.
Combines PDF text retrieval and image retrieval with LLM generation.
"""

from typing import List, Dict, Any, Tuple
from retrieval.vector_store import (
    get_pdf_documents,
    get_image_documents,
    search_with_scores
)
from utils.logger import get_logger

logger = get_logger(__name__)


def retrieve_context(
    vectorstore,
    query: str,
    top_k_pdf: int = 5,
    top_k_images: int = 3
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Retrieve relevant context from both PDF and images.
    
    Args:
        vectorstore: Vector store instance
        query: User query
        top_k_pdf: Number of PDF chunks to retrieve
        top_k_images: Number of images to retrieve
        
    Returns:
        Tuple of (pdf_results, image_results)
    """
    # Retrieve PDF documents
    pdf_docs = get_pdf_documents(vectorstore, query, k=top_k_pdf)
    
    pdf_results = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "source": "floorplans_pdf",
            "page": doc.metadata.get("page", "unknown")
        }
        for doc in pdf_docs
    ]
    
    # Retrieve relevant images
    image_docs = get_image_documents(vectorstore, query, k=top_k_images)
    
    image_results = [
        {
            "path": doc.metadata.get("path", ""),
            "description": doc.metadata.get("description", ""),
            "page": doc.metadata.get("page_number"),
            "filename": doc.metadata.get("filename", ""),
            "relevance": "floorplan"
        }
        for doc in image_docs
        if doc.metadata.get("path")
    ]
    
    logger.info(
        f"Retrieved {len(pdf_results)} PDF chunks and {len(image_results)} images"
    )
    
    return pdf_results, image_results


def format_context_for_prompt(pdf_results: List[Dict[str, Any]]) -> str:
    """
    Format retrieved PDF content into a context string for LLM.
    
    Args:
        pdf_results: List of PDF retrieval results
        
    Returns:
        Formatted context string
    """
    if not pdf_results:
        return "No relevant information found in floorplans document."
    
    context_parts = []
    
    for i, result in enumerate(pdf_results, 1):
        page = result.get("page", "unknown")
        content = result.get("content", "")
        
        context_parts.append(
            f"[Source: Floorplans PDF, Page {page}]\n{content}\n"
        )
    
    return "\n---\n".join(context_parts)


def extract_citations(pdf_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract citation information from retrieval results.
    
    Args:
        pdf_results: List of PDF retrieval results
        
    Returns:
        List of citation dictionaries
    """
    citations = []
    seen_pages = set()
    
    for result in pdf_results:
        page = result.get("page")
        if page and page not in seen_pages:
            citations.append({
                "source": "floorplans_pdf",
                "page": page,
                "villa_type": extract_villa_type_from_content(result.get("content", ""))
            })
            seen_pages.add(page)
    
    return citations


def extract_villa_type_from_content(content: str) -> str:
    """
    Extract villa type from content text.
    
    Args:
        content: Text content
        
    Returns:
        Villa type description or "General information"
    """
    content_upper = content.upper()
    
    # Check for villa type indicators
    if "3BR" in content_upper or "3 BEDROOM" in content_upper:
        if "TYPE B" in content_upper or "POOL" in content_upper:
            return "3BR MIA Type B with Pool"
        return "3BR MIA Type A"
    elif "4BR" in content_upper or "4 BEDROOM" in content_upper:
        if "TYPE B" in content_upper or "POOL" in content_upper:
            return "4BR SHADEA Type B with Pool"
        return "4BR SHADEA Type A"
    elif "5BR" in content_upper or "5 BEDROOM" in content_upper:
        if "TYPE B" in content_upper:
            return "5BR MODEA Type B"
        return "5BR MODEA Type A"
    
    return "General information"


def identify_mentioned_properties(response_text: str) -> List[str]:
    """
    Identify property types mentioned in the response.
    
    Args:
        response_text: LLM response text
        
    Returns:
        List of property identifiers
    """
    properties = []
    response_upper = response_text.upper()
    
    # Map villa types to standardized identifiers
    villa_mappings = {
        "3BR-MIA-TYPE-A": ["3BR", "MIA", "TYPE A"],
        "3BR-MIA-TYPE-B": ["3BR", "MIA", "TYPE B", "POOL"],
        "4BR-SHADEA-TYPE-A": ["4BR", "SHADEA", "TYPE A"],
        "4BR-SHADEA-TYPE-B": ["4BR", "SHADEA", "TYPE B", "POOL"],
        "5BR-MODEA-TYPE-A": ["5BR", "MODEA", "TYPE A"],
        "5BR-MODEA-TYPE-B": ["5BR", "MODEA", "TYPE B"],
    }
    
    for villa_id, keywords in villa_mappings.items():
        # Check if multiple keywords present
        matches = sum(1 for kw in keywords if kw in response_upper)
        if matches >= 2:
            properties.append(villa_id)
    
    return list(set(properties))  # Remove duplicates


def should_include_images(query: str) -> bool:
    """
    Determine if images should be included based on query.
    
    Args:
        query: User query
        
    Returns:
        True if images are likely relevant
    """
    query_lower = query.lower()
    
    # Keywords that suggest visual information is needed
    visual_keywords = [
        "floor plan", "floorplan", "layout", "show", "see", "look",
        "design", "image", "picture", "visual", "configuration",
        "how does", "what does", "ground floor", "first floor"
    ]
    
    return any(keyword in query_lower for keyword in visual_keywords)


def rank_images_by_relevance(
    images: List[Dict[str, Any]],
    query: str,
    pdf_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Rank images by relevance to query and retrieved content.
    
    Args:
        images: List of image results
        query: User query
        pdf_results: Retrieved PDF content
        
    Returns:
        Sorted list of images by relevance
    """
    if not images:
        return []
    
    # Extract mentioned pages from PDF results
    mentioned_pages = set(r.get("page") for r in pdf_results if r.get("page"))
    
    # Score each image
    scored_images = []
    for img in images:
        score = 0
        
        # Higher score if image page matches retrieved PDF pages
        if img.get("page") in mentioned_pages:
            score += 10
        
        # Score based on description matching query
        description = img.get("description", "").lower()
        query_lower = query.lower()
        
        # Check for specific bedroom count
        if "3 bedroom" in query_lower or "3br" in query_lower:
            if "3br" in description:
                score += 5
        if "4 bedroom" in query_lower or "4br" in query_lower:
            if "4br" in description:
                score += 5
        if "5 bedroom" in query_lower or "5br" in query_lower:
            if "5br" in description:
                score += 5
        
        # Check for pool mention
        if "pool" in query_lower and "pool" in description:
            score += 3
        
        scored_images.append((score, img))
    
    # Sort by score descending
    scored_images.sort(key=lambda x: x[0], reverse=True)
    
    return [img for score, img in scored_images]