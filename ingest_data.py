"""
Data ingestion script to process PDF and images and populate vector store.
Run this once before starting the application.
"""

from pathlib import Path
from config import settings
from ingestion.pdf_processor import (
    extract_pdf_pages,
    identify_villa_pages,
    create_chunks_with_metadata
)
from ingestion.image_processor import (
    get_image_files,
    map_images_to_villa_types,
    create_image_index
)
from retrieval.vector_store import (
    initialize_vector_store,
    add_documents_to_vectorstore,
    add_image_metadata_to_vectorstore
)
from utils.logger import get_logger

logger = get_logger(__name__)


def verify_data_files() -> bool:
    """
    Verify that required data files exist.
    
    Returns:
        True if all files exist, False otherwise
    """
    pdf_path = Path(settings.PDF_PATH)
    images_dir = Path(settings.IMAGES_DIR)
    
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {settings.PDF_PATH}")
        return False
    
    if not images_dir.exists():
        logger.error(f"Images directory not found: {settings.IMAGES_DIR}")
        return False
    
    # Check for Rev11 images
    image_files = list(images_dir.glob("*Rev11*.webp"))
    if not image_files:
        logger.warning(f"No Rev11 WebP images found in {settings.IMAGES_DIR}")
    
    logger.info(f"Data files verified: PDF and {len(image_files)} images found")
    return True


def ingest_pdf_data(vectorstore):
    """
    Process and ingest PDF data.
    
    Args:
        vectorstore: Vector store instance
    """
    logger.info("Starting PDF ingestion...")
    
    # Extract pages from PDF
    pages_data = extract_pdf_pages(settings.PDF_PATH)
    logger.info(f"Extracted {len(pages_data)} pages from PDF")
    
    # Identify villa types on pages
    villa_pages = identify_villa_pages(pages_data)
    logger.info(f"Identified villa types across pages: {villa_pages}")
    
    # Create chunks with metadata
    chunks = create_chunks_with_metadata(
        pages_data,
        settings.CHUNK_SIZE,
        settings.CHUNK_OVERLAP
    )
    logger.info(f"Created {len(chunks)} text chunks")
    
    # Add to vector store
    add_documents_to_vectorstore(vectorstore, chunks)
    logger.info("PDF data ingested successfully")
    
    return villa_pages


def ingest_image_data(vectorstore, villa_pages):
    """
    Process and ingest image metadata.
    
    Args:
        vectorstore: Vector store instance
        villa_pages: Dictionary mapping villa types to page numbers
    """
    logger.info("Starting image ingestion...")
    
    # Get image files
    image_files = get_image_files(settings.IMAGES_DIR)
    logger.info(f"Found {len(image_files)} images")
    
    if not image_files:
        logger.warning("No images found, skipping image ingestion")
        return
    
    # Map images to villa types
    villa_images = map_images_to_villa_types(image_files, villa_pages)
    
    for villa_type, images in villa_images.items():
        logger.info(f"{villa_type}: {len(images)} images")
    
    # Create searchable image index
    image_index = create_image_index(settings.IMAGES_DIR)
    logger.info(f"Created index for {len(image_index)} images")
    
    # Add to vector store
    add_image_metadata_to_vectorstore(vectorstore, image_index)
    logger.info("Image data ingested successfully")


def run_ingestion(reset: bool = False):
    """
    Run the complete data ingestion pipeline.
    
    Args:
        reset: If True, reset the vector store before ingestion
    """
    logger.info("="*60)
    logger.info("STARTING DATA INGESTION PIPELINE")
    logger.info("="*60)
    
    # Verify data files exist
    if not verify_data_files():
        logger.error("Data verification failed. Aborting ingestion.")
        return False
    
    try:
        # Initialize vector store
        logger.info(f"Initializing vector store (reset={reset})...")
        vectorstore = initialize_vector_store(reset=reset)
        
        # Ingest PDF data
        villa_pages = ingest_pdf_data(vectorstore)
        
        # Ingest image data
        ingest_image_data(vectorstore, villa_pages)
        
        logger.info("="*60)
        logger.info("DATA INGESTION COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    import sys
    
    # Check if reset flag provided
    reset = "--reset" in sys.argv
    
    if reset:
        logger.warning("Reset flag detected - existing vector store will be deleted")
    
    success = run_ingestion(reset=reset)
    
    if success:
        print("\n✅ Data ingestion completed successfully!")
        print(f"Vector store location: {settings.CHROMA_PERSIST_DIRECTORY}")
        print("\nYou can now start the application with: python app.py")
    else:
        print("\n❌ Data ingestion failed. Check logs for details.")
        sys.exit(1)