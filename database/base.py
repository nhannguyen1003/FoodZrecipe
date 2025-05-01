# TODO: Import all models to ensure they are registered with SQLAlchemy
from database.session import Base
from backend.models.user import User
from backend.models.recipe import Recipe

# All models should be imported here for Alembic