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
from database.session import Base, test_connection
import subprocess

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

@pytest.mark.skip(reason="Manual database initialization test - run separately")
def test_schema_creation_script():
    """Test the schema creation script"""
    logger.info("Testing schema creation script...")
    
    # Get the path to the schema creation script
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    schema_script = os.path.join(data_dir, "put_schemas_to_db.py")
    
    # Verify the script exists
    assert os.path.exists(schema_script), f"Schema script not found at {schema_script}"
    
    # Run the script with dry-run mode (would need to be implemented in the script)
    # This is skipped by default since it would actually modify the database
    logger.info("Schema script exists and can be imported") 