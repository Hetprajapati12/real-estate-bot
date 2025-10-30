"""
Vector store management using ChromaDB.
Handles document embeddings and similarity search.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb # type: ignore
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


# def initialize_embeddings():
#     """
#     Initialize OpenAI embeddings model.
    
#     Returns:
#         OpenAI embeddings instance
#     """
#     return OpenAIEmbeddings(
#         model=settings.EMBEDDING_MODEL,
#         openai_api_key=settings.OPENAI_API_KEY
#     )

def initialize_embeddings():
    """
    Initialize embeddings model.
    Uses HuggingFace sentence-transformers (free, no API key needed).
    
    Returns:
        Embeddings instance
    """
    from langchain_community.embeddings import HuggingFaceEmbeddings
    
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",  # Free, fast, good quality
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )


def initialize_vector_store(
    collection_name: str = "al_badia_villas",
    reset: bool = False
) -> Chroma:
    """
    Initialize or load ChromaDB vector store.
    
    Args:
        collection_name: Name of the collection
        reset: If True, delete existing collection and create new one
        
    Returns:
        Chroma vector store instance
    """
    embeddings = initialize_embeddings()
    
    # Use absolute path to avoid any path issues
    persist_dir = Path(settings.CHROMA_PERSIST_DIRECTORY).absolute()
    persist_dir.mkdir(parents=True, exist_ok=True)
    
    if reset:
        logger.info(f"Resetting vector store: {collection_name}")
        try:
            # Delete the entire directory
            if persist_dir.exists():
                import shutil
                shutil.rmtree(persist_dir)
                persist_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Existing collection deleted")
        except Exception as e:
            logger.debug(f"No existing collection to delete: {e}")
    
    # Create vector store
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(persist_dir)
    )
    
    logger.info(f"Vector store initialized: {collection_name}")
    return vectorstore

def add_documents_to_vectorstore(
    vectorstore: Chroma,
    chunks: List[Dict[str, Any]]
) -> None:
    """
    Add document chunks to vector store.
    
    Args:
        vectorstore: Chroma vector store instance
        chunks: List of chunk dictionaries with text and metadata
    """
    if not chunks:
        logger.warning("No chunks to add to vector store")
        return
    
    documents = [
        Document(
            page_content=chunk["text"],
            metadata=chunk["metadata"]
        )
        for chunk in chunks
    ]
    
    logger.info(f"Adding {len(documents)} documents to vector store")
    
    try:
        vectorstore.add_documents(documents)
        logger.info("Documents added successfully")
    except Exception as e:
        logger.error(f"Error adding documents: {e}")
        raise


def add_image_metadata_to_vectorstore(
    vectorstore: Chroma,
    image_index: List[Dict[str, Any]]
) -> None:
    """
    Add image metadata with descriptions to vector store for retrieval.
    
    Args:
        vectorstore: Chroma vector store instance
        image_index: List of image metadata with descriptions
    """
    if not image_index:
        logger.warning("No images to index")
        return
    
    documents = []
    
    for img_meta in image_index:
        if "searchable_text" in img_meta:
            doc = Document(
                page_content=img_meta["searchable_text"],
                metadata={
                    "source_type": "floorplan_image",
                    "filename": img_meta["filename"],
                    "path": img_meta["path"],
                    "page_number": img_meta.get("page_number"),
                    "description": img_meta.get("description", "")
                }
            )
            documents.append(doc)
    
    if documents:
        logger.info(f"Adding {len(documents)} image metadata entries to vector store")
        try:
            vectorstore.add_documents(documents)
            logger.info("Image metadata indexed successfully")
        except Exception as e:
            logger.error(f"Error indexing images: {e}")
            raise


def search_vectorstore(
    vectorstore: Chroma,
    query: str,
    k: int = None,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Document]:
    """
    Search vector store for similar documents.
    
    Args:
        vectorstore: Chroma vector store instance
        query: Search query
        k: Number of results to return
        filter_dict: Optional metadata filter
        
    Returns:
        List of Document objects with content and metadata
    """
    k = k or settings.TOP_K_RESULTS
    
    try:
        if filter_dict:
            results = vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = vectorstore.similarity_search(query, k=k)
        
        logger.debug(f"Retrieved {len(results)} results for query: {query[:50]}...")
        return results
        
    except Exception as e:
        logger.error(f"Error searching vector store: {e}")
        return []


def search_with_scores(
    vectorstore: Chroma,
    query: str,
    k: int = None,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[tuple]:
    """
    Search vector store and return results with similarity scores.
    
    Args:
        vectorstore: Chroma vector store instance
        query: Search query
        k: Number of results to return
        filter_dict: Optional metadata filter
        
    Returns:
        List of tuples (Document, score)
    """
    k = k or settings.TOP_K_RESULTS
    
    try:
        if filter_dict:
            results = vectorstore.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = vectorstore.similarity_search_with_score(query, k=k)
        
        # Filter by similarity threshold
        filtered_results = [
            (doc, score) for doc, score in results
            if score <= (1 - settings.SIMILARITY_THRESHOLD)  # Chroma uses distance, not similarity
        ]
        
        logger.debug(
            f"Retrieved {len(filtered_results)}/{len(results)} results "
            f"above threshold for query: {query[:50]}..."
        )
        
        return filtered_results
        
    except Exception as e:
        logger.error(f"Error searching with scores: {e}")
        return []


def get_pdf_documents(vectorstore: Chroma, query: str, k: int = 3) -> List[Document]:
    """
    Search only PDF documents (text content).
    
    Args:
        vectorstore: Chroma vector store instance
        query: Search query
        k: Number of results
        
    Returns:
        List of PDF document results
    """
    return search_vectorstore(
        vectorstore,
        query,
        k=k,
        filter_dict={"source_type": "floorplans_pdf"}
    )


def get_image_documents(vectorstore: Chroma, query: str, k: int = 3) -> List[Document]:
    """
    Search only image metadata.
    
    Args:
        vectorstore: Chroma vector store instance
        query: Search query
        k: Number of results
        
    Returns:
        List of image metadata results
    """
    return search_vectorstore(
        vectorstore,
        query,
        k=k,
        filter_dict={"source_type": "floorplan_image"}
    )