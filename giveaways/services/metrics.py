"""
Performance metrics for giveaways services.

This module provides utilities for tracking performance metrics for giveaway operations:
- Query execution time
- Database load monitoring
- Batch processing statistics
"""

import time
import logging
import threading
import functools
from typing import Dict, Any, Optional, List, Callable
from django.utils import timezone

logger = logging.getLogger(__name__)

# Thread-local storage for metrics
_local = threading.local()


class MetricsCollector:
    """
    Collects performance metrics for giveaway operations.
    
    Provides methods for tracking execution time, query counts, and other performance metrics.
    Data is stored in thread-local storage to ensure thread safety.
    """
    
    @staticmethod
    def start_operation(operation_name: str) -> None:
        """
        Start tracking metrics for an operation.
        
        Args:
            operation_name: Name of the operation to track
        """
        if not hasattr(_local, 'metrics'):
            _local.metrics = {}
            
        _local.metrics[operation_name] = {
            'start_time': time.time(),
            'queries': 0,
            'completed': False,
            'error': None,
            'batch_size': 0,
            'processed_items': 0,
            'timestamp': timezone.now().isoformat()
        }
    
    @staticmethod
    def end_operation(operation_name: str, error: Optional[Exception] = None) -> Dict[str, Any]:
        """
        End tracking metrics for an operation.
        
        Args:
            operation_name: Name of the operation
            error: Exception if operation failed
            
        Returns:
            Dict containing metrics for the operation
        """
        if not hasattr(_local, 'metrics') or operation_name not in _local.metrics:
            logger.warning(f"No metrics found for operation: {operation_name}")
            return {}
            
        metrics = _local.metrics[operation_name]
        metrics['end_time'] = time.time()
        metrics['duration'] = metrics['end_time'] - metrics['start_time']
        metrics['completed'] = error is None
        metrics['error'] = str(error) if error else None
        
        # Log metrics
        if error:
            logger.error(f"Operation {operation_name} failed after {metrics['duration']:.2f}s: {str(error)}")
        else:
            logger.info(
                f"Operation {operation_name} completed in {metrics['duration']:.2f}s "
                f"(processed {metrics['processed_items']}/{metrics['batch_size']} items)"
            )
        
        return metrics
    
    @staticmethod
    def increment_counter(operation_name: str, counter_name: str, increment: int = 1) -> None:
        """
        Increment a counter for an operation.
        
        Args:
            operation_name: Name of the operation
            counter_name: Name of the counter to increment
            increment: Amount to increment by
        """
        if not hasattr(_local, 'metrics') or operation_name not in _local.metrics:
            logger.warning(f"No metrics found for operation: {operation_name}")
            return
            
        metrics = _local.metrics[operation_name]
        if counter_name not in metrics:
            metrics[counter_name] = 0
            
        metrics[counter_name] += increment
    
    @staticmethod
    def set_batch_size(operation_name: str, batch_size: int) -> None:
        """
        Set the batch size for an operation.
        
        Args:
            operation_name: Name of the operation
            batch_size: Size of the batch being processed
        """
        if not hasattr(_local, 'metrics') or operation_name not in _local.metrics:
            logger.warning(f"No metrics found for operation: {operation_name}")
            return
            
        _local.metrics[operation_name]['batch_size'] = batch_size
    
    @staticmethod
    def get_metrics(operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for an operation or all operations.
        
        Args:
            operation_name: Name of the operation or None for all operations
            
        Returns:
            Dict containing metrics
        """
        if not hasattr(_local, 'metrics'):
            return {}
            
        if operation_name:
            return _local.metrics.get(operation_name, {})
        else:
            return _local.metrics


def track_operation(operation_name: str) -> Callable:
    """
    Decorator to track metrics for an operation.
    
    Args:
        operation_name: Name of the operation to track
        
    Returns:
        Decorated function with metrics tracking
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            MetricsCollector.start_operation(operation_name)
            
            try:
                result = func(*args, **kwargs)
                MetricsCollector.end_operation(operation_name)
                return result
            except Exception as e:
                MetricsCollector.end_operation(operation_name, error=e)
                raise
                
        return wrapper
    return decorator
