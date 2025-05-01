#!/usr/bin/env python3
"""
Script to test database connection and initialization
"""
import sys
import os
import logging

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import test_connection, create_tables
from database.init_db import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Test database connection and initialization
    """
    logger.info("Testing database connection...")
    if test_connection():
        logger.info("Database connection successful!")
        
        logger.info("Testing table creation...")
        create_tables()
        logger.info("Table creation successful!")
        
        logger.info("Running database initialization...")
        init_db()
        logger.info("Database initialization complete!")
    else:
        logger.error("Database connection failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 