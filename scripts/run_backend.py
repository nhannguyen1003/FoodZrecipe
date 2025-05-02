#!/usr/bin/env python
"""
Run script for the FoodZrecipe backend.
This script performs pre-flight checks and then starts the FastAPI server.
"""

import sys
import os
import time
import logging
import subprocess

# Add the parent directory to the path so we can import from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from database.session import test_connection
from backend.core.logging import logger

def check_database():
    """Check if the database is accessible"""
    logger.info("Checking database connection...")
    
    retries = 3
    for i in range(retries):
        if test_connection():
            logger.info("Database connection successful")
            return True
        
        if i < retries - 1:
            logger.warning(f"Database connection failed, retrying in 2 seconds (attempt {i+1}/{retries})")
            time.sleep(2)
    
    logger.error("Could not connect to the database after multiple attempts")
    return False

def check_environment():
    """Check environment variables and configuration"""
    logger.info("Checking environment configuration...")
    
    required_vars = [
        "POSTGRES_USER", 
        "POSTGRES_PASSWORD", 
        "POSTGRES_DB", 
        "POSTGRES_HOST", 
        "POSTGRES_PORT",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
        
    logger.info("Environment configuration check passed")
    return True

def run_server():
    """Run the FastAPI server using uvicorn"""
    try:
        logger.info(f"Starting FastAPI server in {'debug' if settings.DEBUG else 'production'} mode")
        
        # Build the uvicorn command
        uvicorn_cmd = [
            "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        # Add reload flag in debug mode
        if settings.DEBUG:
            uvicorn_cmd.append("--reload")
        
        # Execute uvicorn
        subprocess.run(uvicorn_cmd)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Error starting the server: {e}")
        return False
        
    return True

def main():
    """Main entry point for the script"""
    logger.info("=" * 50)
    logger.info("FoodZrecipe Backend Server Startup")
    logger.info("=" * 50)
    
    # Run pre-flight checks
    checks_passed = True
    
    if not check_environment():
        checks_passed = False
    
    if not check_database():
        checks_passed = False
    
    if not checks_passed:
        logger.error("Pre-flight checks failed, exiting")
        sys.exit(1)
    
    # Run the server
    logger.info("All pre-flight checks passed")
    run_server()

if __name__ == "__main__":
    main() 