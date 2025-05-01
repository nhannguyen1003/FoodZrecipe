import logging
from sqlalchemy.exc import SQLAlchemyError
from database.session import engine, SessionLocal, create_tables, test_connection
from backend.models.user import User, UserRole
from backend.models.recipe import Recipe
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def init_db() -> bool:
    """
    Initialize the database by creating all tables and adding initial data.
    This should be called during application startup.
    """
    try:
        logger.info("Creating database tables...")
        # Test database connection
        if not test_connection():
            logger.error("Failed to connect to the database. Aborting initialization.")
            return False
        
        # Create all tables
        create_tables()
        logger.info("Database tables created successfully")
        
        # Add initial data if needed
        db = SessionLocal()
        try:
            # Only add admin user if no users exist
            user_count = db.query(User).count()
            if user_count == 0:
                logger.info("Adding initial admin user...")
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash("adminpassword"),
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.add(admin_user)
                
                # Add a sample regular user
                regular_user = User(
                    username="user",
                    email="user@example.com",
                    hashed_password=get_password_hash("userpassword"),
                    role=UserRole.REGULAR,
                    is_active=True
                )
                db.add(regular_user)
                db.flush()  # Flush to get IDs
                
                # Add some sample recipes
                sample_recipe = Recipe(
                    title="Classic Pancakes",
                    description="Fluffy and delicious breakfast pancakes",
                    ingredients=["1 cup all-purpose flour", "2 tbsp sugar", "2 tsp baking powder", 
                                "1/2 tsp salt", "1 egg", "1 cup milk", "2 tbsp vegetable oil"],
                    instructions=["Whisk dry ingredients together", 
                                "Beat egg, milk, and oil in another bowl", 
                                "Combine wet and dry ingredients, stir until just mixed", 
                                "Heat a lightly oiled griddle over medium-high heat", 
                                "Pour batter onto the griddle, cook until bubbles form", 
                                "Flip and cook until browned on the other side"],
                    image_url="https://example.com/pancakes.jpg",
                    categories=["breakfast", "quick", "vegetarian"],
                    prep_time=10,
                    cook_time=15,
                    servings=4,
                    user_id=regular_user.id,  # Use the actual ID
                    feature_vector=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]  # Placeholder vector
                )
                db.add(sample_recipe)
                
                db.commit()
                logger.info("Initial data added successfully")
                return True
            else:
                logger.info("Database already has users, skipping initial data creation")
                return True
                
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding initial data: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    # Can be run directly for manual initialization
    logger.info("Initializing database...")
    success = init_db()
    if success:
        logger.info("Database initialization completed successfully")
    else:
        logger.error("Database initialization failed") 