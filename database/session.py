# Database connection and session management
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=settings.DEBUG  # SQL query logging based on DEBUG setting
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    """
    Dependency that provides a database session for FastAPI routes.
    Usage in FastAPI routes:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        logger.debug("Database session yielded successfully")
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Database session closed")

def create_tables():
    """
    Create all tables defined in models.
    Call this function during application startup.
    """
    try:
        # Import all models to ensure they are registered with SQLAlchemy
        from database.base import Base
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def test_connection():
    """
    Test database connection.
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
    finally:
        db.close()