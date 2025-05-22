"""
Base utilities for giveaways services.

This module contains common utilities used across all service modules:
- Logging decorators
- Performance tracking
- Common exceptions
"""

import time
import functools
import logging

logger = logging.getLogger(__name__)


def log_execution_time(func):
    """
    Decorator to log function execution time.
    
    Logs the execution time of the decorated function at INFO level.
    Also logs any exceptions that occur during execution at ERROR level.
    
    Args:
        func: The function to decorate
        
    Returns:
        Wrapped function that logs execution time
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__
        logger.info(f"Starting {func_name}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func_name} completed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func_name} failed after {execution_time:.2f} seconds with error: {str(e)}")
            raise
            
    return wrapper


class ServiceError(Exception):
    """Base exception for service-related errors."""
    pass


class SelectionError(ServiceError):
    """Exception raised when winner selection fails."""
    pass
