import logging
import datetime
from sqlalchemy.exc import SQLAlchemyError
from database.session import engine, SessionLocal, create_tables, test_connection
from backend.models.user import User, UserRole
from backend.models.recipe import Recipe
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import importlib
import os
import sys
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def init_db(db: Session) -> None:
    """Initialize the database with required initial data"""
    # Check if we already have an admin user
    user = db.query(User).filter(User.email == "admin@example.com").first()
    
    if user:
        logger.info("Database already initialized, skipping initialization")
        return
    
    logger.info("Creating initial admin user")
    
    # Create default admin user
    admin_obj = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("admin"),
        is_active=True,
        role=UserRole.ADMIN
    )
    
    db.add(admin_obj)
    db.commit()
    
    logger.info("Initial admin user created")
    
def run_data_seeding():
    """Run data seeding script to populate database with sample data"""
    logger.info("Running data seeding script...")
    
    try:
        # Check if scripts directory exists
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
        seed_script_path = os.path.join(scripts_dir, "seed_db.py")
        
        if os.path.exists(seed_script_path):
            # Run the seeding script as a subprocess
            subprocess.run([sys.executable, seed_script_path], check=True)
            logger.info("Data seeding completed")
        else:
            logger.warning(f"Seed script not found at {seed_script_path}")
    
    except Exception as e:
        logger.error(f"Error running data seeding: {e}")
        # Continue with application startup even if seeding fails
    
if __name__ == "__main__":
    # Can be run directly for manual initialization
    logger.info("Initializing database...")
    db = SessionLocal()
    
    try:
        init_db(db)
        
        # Run data seeding if command line argument is provided
        if len(sys.argv) > 1 and sys.argv[1] == "--seed":
            run_data_seeding()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        db.close()
        logger.info("Database initialization completed successfully") 