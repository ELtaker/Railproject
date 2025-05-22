"""
Services package for giveaways.

This package contains service modules for complex business logic:
- base.py: Common utilities like logging decorators
- winner_selection.py: Core winner selection logic
- metrics.py: Performance tracking utilities
"""

from .base import log_execution_time
from .winner_selection import select_random_winner_scalable, process_winners_batch
