"""
Database verification script to test the database models and SQLAlchemy setup
"""
import logging
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from database.session import engine, SessionLocal, Base, create_tables, test_connection
from database.base import register_models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_database_connection():
    """Verify database connection"""
    logger.info("Verifying database connection...")
    connected = test_connection()
    if connected:
        logger.info("Database connection successful")
        return True
    else:
        logger.error("Database connection failed")
        return False

def verify_tables_exist():
    """Verify all tables are defined in the database"""
    logger.info("Verifying database tables...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    models = register_models()
    expected_tables = [model.__tablename__ for model in models]
    
    logger.info(f"Existing tables: {', '.join(existing_tables)}")
    logger.info(f"Expected tables: {', '.join(expected_tables)}")
    
    missing_tables = [table for table in expected_tables if table not in existing_tables]
    if missing_tables:
        logger.warning(f"Missing tables: {', '.join(missing_tables)}")
        return False
    else:
        logger.info("All expected tables exist")
        return True

def verify_table_structure():
    """Verify table structure contains all expected columns"""
    logger.info("Verifying table structure...")
    
    models = register_models()
    inspector = inspect(engine)
    
    for model in models:
        table_name = model.__tablename__
        columns = inspector.get_columns(table_name)
        column_names = [column["name"] for column in columns]
        
        # Get model columns
        model_columns = [column.name for column in model.__table__.columns]
        
        logger.info(f"Table {table_name} columns: {', '.join(column_names)}")
        
        missing_columns = [col for col in model_columns if col not in column_names]
        if missing_columns:
            logger.warning(f"Table {table_name} is missing columns: {', '.join(missing_columns)}")
            return False
    
    logger.info("All tables have expected columns")
    return True

def run_verification():
    """Run all verification steps"""
    if not verify_database_connection():
        logger.error("Database verification failed: Unable to connect to database")
        return False
    
    # Only check tables if connected to the database
    if not verify_tables_exist():
        logger.warning("Tables verification failed - creating tables...")
        try:
            create_tables()
            if verify_tables_exist():
                logger.info("Tables created successfully")
            else:
                logger.error("Failed to create tables")
                return False
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    if not verify_table_structure():
        logger.error("Table structure verification failed")
        return False
    
    logger.info("All verification steps passed successfully")
    return True

if __name__ == "__main__":
    logger.info("Starting database verification...")
    result = run_verification()
    
    if result:
        logger.info("Database setup is verified and ready to use")
        sys.exit(0)
    else:
        logger.error("Database verification failed. Please check the logs for details.")
        sys.exit(1) 