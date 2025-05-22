"""
Celery configuration for Raildrops.

This module sets up Celery for asynchronous task processing,
including winner selection for giveaways.
"""

import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery app
app = Celery('raildrops')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Default configuration
app.conf.update(
    # Task result settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Oslo',
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Task routing for winner selection
    task_routes={
        'giveaways.select_winner_task': {'queue': 'giveaway_winners'},
        'giveaways.select_winners_batch': {'queue': 'giveaway_control'},
        'giveaways.summarize_winner_selection': {'queue': 'giveaway_control'},
    },
    
    # Rate limits to prevent database overload
    task_annotations={
        'giveaways.select_winner_task': {'rate_limit': '10/s'},
        'giveaways.select_winners_batch': {'rate_limit': '1/s'},
    }
)

@app.task(bind=True)
def debug_task(self):
    """Simple task to verify Celery is working properly."""
    print(f'Request: {self.request!r}')
