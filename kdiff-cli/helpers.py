import logging
import os
from typing import Optional

def get_logger(name: str = "kdiff") -> logging.Logger:
    """
    Get a logger instance with level set from KDIFF_LOGLEVEL environment variable.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured yet
    if not logger.handlers:
        # Get log level from environment variable
        log_level_str = os.getenv("KDIFF_LOGLEVEL", "INFO").upper()
        
        # Map string levels to logging constants
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        log_level = level_mapping.get(log_level_str, logging.INFO)
        
        # Configure the logger
        logger.setLevel(log_level)
        
        # Create console handler if none exists
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger 