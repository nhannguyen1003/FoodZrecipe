from sqlalchemy.orm import Session
import logging
from database.session import SessionLocal
from database.repositories.recipe_repository import recipe_repository
from backend.services.lsh_service import lsh_service

logger = logging.getLogger(__name__)

def initialize_lsh_indices():
    """
    Initialize LSH indices at application startup
    
    This is called when the FastAPI application starts up
    to load all recipes into the FAISS LSH indices for efficient search.
    """
    logger.info("Initializing LSH indices...")
    
    try:
        db = SessionLocal()
        try:
            # Initialize recipe repository's indices
            recipe_repository.load_faiss_indices(db)
            
            # Get statistics for logging
            text_index_size = getattr(recipe_repository.text_index, 'ntotal', 0)
            image_index_size = getattr(recipe_repository.image_index, 'ntotal', 0)
            
            logger.info(f"LSH indices initialized successfully: {text_index_size} text vectors, {image_index_size} image vectors")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error initializing LSH indices: {str(e)}")
        # Don't fail application startup if indices can't be built
        # The application can still work with standard search

def init_app():
    """
    Initialize the application
    
    Called when the FastAPI application starts
    """
    # Initialize FAISS LSH indices
    initialize_lsh_indices() 