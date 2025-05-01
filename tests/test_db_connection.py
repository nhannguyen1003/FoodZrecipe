#!/usr/bin/env python3
"""
Script to test database connection and initialization
"""
import sys
import os
import logging

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Test database connection and initialization
    """
    try:
        # Only import here after sys.path is set
        from config import settings
        from database.session import test_connection, create_tables
        from database.init_db import init_db
        
        logger.info("Successfully imported modules")
        logger.info(f"Using database URL: {settings.DATABASE_URL}")
        
        logger.info("Testing database connection...")
        connection_successful = test_connection()
        
        if connection_successful:
            logger.info("Database connection successful!")
            
            logger.info("Testing table creation...")
            create_tables()
            logger.info("Table creation successful!")
            
            logger.info("Running database initialization...")
            init_successful = init_db()
            if init_successful:
                logger.info("Database initialization complete!")
            else:
                logger.error("Database initialization failed!")
                sys.exit(1)
        else:
            logger.error("Database connection failed!")
            sys.exit(1)
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error(f"Python path: {sys.path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 