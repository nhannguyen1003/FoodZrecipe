import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from config import settings

def setup_logging():
    """
    Configure application logging
    
    Sets up structured logging with different handlers based on the environment:
    - Console logging in development
    - File + console logging in production
    - Different log levels based on DEBUG setting
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Create the logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Main application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
    app_logger.propagate = False
    
    # Clear existing handlers to avoid duplicate logs
    if app_logger.handlers:
        app_logger.handlers.clear()
    
    # Create formatters
    verbose_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    simple_formatter = logging.Formatter(
        "%(levelname)s: %(message)s"
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter if settings.DEBUG else verbose_formatter)
    console_handler.setLevel(log_level)
    app_logger.addHandler(console_handler)
    
    # File handler (only in production)
    if not settings.DEBUG:
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, "app.log"),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(verbose_formatter)
        file_handler.setLevel(logging.INFO)
        app_logger.addHandler(file_handler)
        
        # Error log file for ERROR and above
        error_file_handler = RotatingFileHandler(
            os.path.join(logs_dir, "error.log"),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        error_file_handler.setFormatter(verbose_formatter)
        error_file_handler.setLevel(logging.ERROR)
        app_logger.addHandler(error_file_handler)
    
    # Configure SQLAlchemy logging
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.setLevel(logging.WARNING if settings.DEBUG else logging.ERROR)
    
    # Other third-party libraries
    # Set conservative log levels for third-party libraries to avoid log spam
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    # Return the configured logger
    return app_logger

# Create a shared logger instance
logger = setup_logging() 