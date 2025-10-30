"""
Image processing and indexing for floorplan images.
Maps images to villa types and specifications.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)


def get_image_files(images_dir: str, pattern: str = "*Rev11*.webp") -> List[Path]:
    """
    Get all Rev11 image files from directory.
    
    Args:
        images_dir: Directory containing images
        pattern: Glob pattern for files (default: Rev11 WebP files)
        
    Returns:
        List of Path objects for matching images
    """
    images_path = Path(images_dir)
    
    if not images_path.exists():
        logger.warning(f"Images directory not found: {images_dir}")
        return []
    
    image_files = list(images_path.glob(pattern))
    logger.info(f"Found {len(image_files)} images matching pattern: {pattern}")
    
    return sorted(image_files)


def extract_page_number_from_filename(filename: str) -> Optional[int]:
    """
    Extract page number from image filename.
    Example: AlBadia_Floorplans_A3_Rev11-7.webp -> 7
    
    Args:
        filename: Image filename
        
    Returns:
        Page number or None if not found
    """
    parts = filename.split('-')
    if len(parts) >= 2:
        try:
            # Get the last part before extension and extract number
            page_part = parts[-1].split('.')[0]
            return int(page_part)
        except ValueError:
            pass
    
    return None


def create_image_metadata(image_path: Path) -> Dict[str, Any]:
    """
    Create metadata for a floorplan image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary containing image metadata
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            format_type = img.format
    except Exception as e:
        logger.error(f"Error reading image {image_path}: {e}")
        width, height, format_type = None, None, None
    
    page_number = extract_page_number_from_filename(image_path.name)
    
    metadata = {
        "filename": image_path.name,
        "path": str(image_path),
        "page_number": page_number,
        "width": width,
        "height": height,
        "format": format_type,
        "source_type": "floorplan_image"
    }
    
    return metadata


def map_images_to_villa_types(
    image_files: List[Path],
    villa_pages: Dict[str, List[int]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Map floorplan images to villa types based on page numbers.
    
    Args:
        image_files: List of image file paths
        villa_pages: Dictionary mapping villa types to page numbers
        
    Returns:
        Dictionary mapping villa types to list of image metadata
    """
    villa_images = {villa_type: [] for villa_type in villa_pages.keys()}
    
    for image_path in image_files:
        page_num = extract_page_number_from_filename(image_path.name)
        
        if page_num is None:
            logger.warning(f"Could not extract page number from: {image_path.name}")
            continue
        
        metadata = create_image_metadata(image_path)
        
        # Find which villa type(s) this page corresponds to
        for villa_type, pages in villa_pages.items():
            if page_num in pages:
                villa_images[villa_type].append(metadata)
                logger.debug(f"Mapped {image_path.name} to {villa_type}")
    
    return villa_images


def create_image_index(images_dir: str) -> List[Dict[str, Any]]:
    """
    Create a searchable index of all floorplan images.
    
    Args:
        images_dir: Directory containing images
        
    Returns:
        List of image metadata dictionaries
    """
    image_files = get_image_files(images_dir)
    
    if not image_files:
        logger.warning("No images found for indexing")
        return []
    
    image_index = []
    
    for image_path in image_files:
        metadata = create_image_metadata(image_path)
        
        # Add searchable text description
        page_num = metadata.get("page_number")
        if page_num:
            # Generate description based on page number
            description = generate_image_description(page_num, image_path.name)
            metadata["description"] = description
            metadata["searchable_text"] = description
        
        image_index.append(metadata)
    
    logger.info(f"Created image index with {len(image_index)} entries")
    return image_index


def generate_image_description(page_num: int, filename: str) -> str:
    """
    Generate descriptive text for an image based on page number.
    Maps to known Al Badia Villas structure.
    
    Args:
        page_num: PDF page number
        filename: Image filename
        
    Returns:
        Descriptive text for the image
    """
    # Known page mappings for Al Badia Villas (pages 4-8 contain villa details)
    descriptions = {
        4: "3BR MIA Type A floorplan - Ground and first floor layout without pool",
        5: "3BR MIA Type B floorplan - Ground and first floor layout with swimming pool",
        6: "4BR SHADEA Type A floorplan - Ground and first floor layout without pool",
        7: "4BR SHADEA Type B floorplan - Ground and first floor layout with swimming pool",
        8: "5BR MODEA Type A and Type B floorplans - Ground and first floor layouts",
    }
    
    base_description = descriptions.get(
        page_num,
        f"Al Badia Villas floorplan page {page_num}"
    )
    
    # Add pool indicator if in filename
    if "pool" in filename.lower() or (page_num in [5, 7]):
        base_description += " with pool"
    
    return base_description


def get_images_for_villa_type(
    villa_type: str,
    villa_images: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Retrieve all images for a specific villa type.
    
    Args:
        villa_type: Villa type identifier
        villa_images: Villa-to-images mapping
        
    Returns:
        List of image metadata for the villa type
    """
    return villa_images.get(villa_type, [])


def get_images_by_page(page_number: int, image_index: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get all images for a specific page number.
    
    Args:
        page_number: PDF page number
        image_index: Complete image index
        
    Returns:
        List of matching image metadata
    """
    return [
        img for img in image_index
        if img.get("page_number") == page_number
    ]