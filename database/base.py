# Import all models to ensure they are registered with SQLAlchemy
from database.session import Base

# Import all models here
def register_models():
    """Register all models with SQLAlchemy"""
    # Import models only when needed to avoid circular imports
    from backend.models.user import User
    from backend.models.recipe import Recipe
    
    # Return a list of models for reference if needed
    return [User, Recipe]

# All models should be imported here for Alembic