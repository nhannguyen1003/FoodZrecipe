from sqlalchemy.orm import Session
import logging
import os
import sys
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

def run_data_seeding_if_needed():
    """
    Run data seeding process if the database is empty or FORCE_SEED environment variable is set
    """
    try:
        # Check if we should run data seeding
        force_seed = os.environ.get("FORCE_SEED", "").lower() in ("true", "1", "yes")
        
        # Check if database has recipes
        db = SessionLocal()
        try:
            from backend.models.recipe import Recipe
            recipe_count = db.query(Recipe).count()
            
            if recipe_count == 0 or force_seed:
                logger.info(f"Running data seeding (recipe_count={recipe_count}, force_seed={force_seed})")
                
                # Import and run the seeding function
                scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")
                sys.path.insert(0, scripts_dir)
                
                try:
                    from seed_data import seed_database
                    seed_database()
                except ImportError:
                    logger.error("Could not import seed_database function. Make sure scripts/seed_data.py exists.")
            else:
                logger.info(f"Skipping data seeding (recipe_count={recipe_count}, force_seed={force_seed})")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in data seeding process: {str(e)}")
        # Don't fail application startup if seeding fails

def init_app():
    """
    Initialize the application
    
    Called when the FastAPI application starts
    """
    # Run data seeding if needed
    run_data_seeding_if_needed()
    
    # Initialize FAISS LSH indices
    initialize_lsh_indices() 