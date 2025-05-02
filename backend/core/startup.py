from sqlalchemy.orm import Session
import logging
import os
import sys
from pathlib import Path
from database.session import SessionLocal
from database.repositories.recipe_repository import recipe_repository
from backend.services.lsh_service import lsh_service
from backend.services.multi_field_search_service import multi_field_search_service

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
            # Check if there are recipes in the database
            from backend.models.recipe import Recipe
            recipe_count = db.query(Recipe).count()
            
            if recipe_count == 0:
                logger.warning("No recipes found in database. LSH indices not initialized.")
                return
                
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

def initialize_multi_field_search():
    """
    Initialize multi-field search indices at application startup
    
    This loads field-specific embeddings and creates FAISS indices for them
    """
    logger.info("Initializing multi-field search indices...")
    
    try:
        db = SessionLocal()
        try:
            # Check if there are recipes in the database
            from backend.models.recipe import Recipe
            recipe_count = db.query(Recipe).count()
            
            if recipe_count == 0:
                logger.warning("No recipes found in database. Multi-field search indices not initialized.")
                return
                
            # Build multi-field search indices
            multi_field_search_service.initialize_indices()
            multi_field_search_service.build_indices(db)
            
            # Initialize recipe repository's multi-field indices
            recipe_repository.load_multi_field_indices(db)
            
            # Get statistics for logging
            title_index_size = getattr(recipe_repository.title_index, 'ntotal', 0)
            ingredients_index_size = getattr(recipe_repository.ingredients_index, 'ntotal', 0)
            instructions_index_size = getattr(recipe_repository.instructions_index, 'ntotal', 0)
            
            logger.info(f"Multi-field search indices initialized successfully: "
                       f"{title_index_size} title vectors, "
                       f"{ingredients_index_size} ingredients vectors, "
                       f"{instructions_index_size} instructions vectors")
            
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error initializing multi-field search indices: {str(e)}")
        # Don't fail application startup if indices can't be built

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
                
                # Check if the sample_recipes_with_hashed.json file exists
                data_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "data" / "db"
                sample_file = data_dir / "sample_recipes_with_hashed.json"
                
                if not sample_file.exists():
                    logger.error(f"Sample recipes file not found at {sample_file}, seeding cannot be completed")
                    return
                    
                logger.info(f"Found sample recipes file at {sample_file}")
                
                # Use the data initialization scripts
                data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
                
                try:
                    import subprocess
                    
                    # Run the schema creation script if needed
                    schema_script = os.path.join(data_dir, "put_schemas_to_db.py")
                    logger.info(f"Running schema creation script: {schema_script}")
                    subprocess.run([sys.executable, schema_script], check=True)
                    
                    # Run the data loading script
                    data_script = os.path.join(data_dir, "put_data_to_db.py")
                    logger.info(f"Running data loading script: {data_script}")
                    subprocess.run([sys.executable, data_script], check=True)
                    
                    logger.info("Data seeding completed successfully")
                except Exception as e:
                    logger.error(f"Error running data initialization scripts: {e}")
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
    # Skip automatic data seeding (comment out to re-enable)
    # run_data_seeding_if_needed()
    logger.info("Automatic data seeding disabled - using manually initialized data")
    
    # Initialize FAISS LSH indices
    initialize_lsh_indices()
    
    # Initialize multi-field search indices
    initialize_multi_field_search() 