from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.session import get_db, test_connection
from config import settings
import logging
from typing import Dict

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=Dict[str, str])
def health_check():
    """
    Basic health check endpoint.
    Used for monitoring and verifying the API is running.
    """
    return {"status": "ok", "message": "API is up and running"}

@router.get("/db", response_model=Dict[str, str])
def database_health_check(db: Session = Depends(get_db)):
    """
    Database health check endpoint.
    Verifies that the database connection is working.
    """
    try:
        if test_connection():
            return {"status": "ok", "message": "Database connection successful"}
        else:
            return {"status": "error", "message": "Database connection failed"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "error", "message": f"Database connection error: {str(e)}"}

@router.get("/info", response_model=Dict[str, str])
def api_info():
    """
    Returns information about the API.
    """
    return {
        "version": "1.0.0",
        "name": "FoodZrecipe API",
        "environment": "development" if settings.DEBUG else "production",
        "api_prefix": settings.API_PREFIX
    } 