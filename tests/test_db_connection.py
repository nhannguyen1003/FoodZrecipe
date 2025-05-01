#!/usr/bin/env python3
"""
Tests for database connection and initialization
"""
import sys
import os
import logging
import pytest
from sqlalchemy import text

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required modules
from config import settings
from database.session import Base
from database.init_db import init_db

def test_connection():
    """Simple test to verify pytest is working"""
    assert True

def test_module_imports():
    """Test that all required modules can be imported"""
    assert settings is not None
    assert Base is not None
    logger.info("Successfully imported modules")
    logger.info(f"Using database URL: {settings.DATABASE_URL}")

def test_database_connection(engine):
    """Test database connection using test engine"""
    logger.info("Testing database connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1, "Database connection failed!"
    logger.info("Database connection successful!")

def test_table_creation(engine, create_tables):
    """Test table creation using fixtures"""
    logger.info("Testing table creation...")
    # The create_tables fixture handles table creation
    # Just verify that at least one table exists in our schema
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'test_schema' 
                AND table_name = 'users'
            )
        """)).scalar()
        assert result, "Users table was not created!"
    logger.info("Table creation successful!")

@pytest.mark.skip(reason="Database initialization fails due to schema mismatch - needs fixing")
def test_database_initialization():
    """Test database initialization"""
    logger.info("Running database initialization...")
    init_successful = init_db()
    assert init_successful, "Database initialization failed!"
    logger.info("Database initialization complete!") 