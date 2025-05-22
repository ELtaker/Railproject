"""Django project configuration initialization.

This module initializes Celery for asynchronous task processing.
"""

# Import the Celery application
from .celery import app as celery_app

__all__ = ['celery_app']
