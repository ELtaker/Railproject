"""
Services package for giveaways.

This package contains service modules for complex business logic:
- base.py: Common utilities like logging decorators
- winner_selection.py: Core winner selection logic
- metrics.py: Performance tracking utilities

The package also exposes key functions from the parent services.py module.
"""

from .base import log_execution_time
from .winner_selection import select_random_winner_scalable, process_winners_batch

# Import and expose key functions from the parent services.py module
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the validate_entry function from the parent module
try:
    from ..services import validate_entry, cities_match, normalize_city, select_random_winner, can_select_winners_for_expired_giveaways
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import from parent services.py: {e}")
    
    # Define fallback functions to prevent crashes
    def validate_entry(*args, **kwargs):
        return {"success": False, "error": "Validation service unavailable. Please try again later."}
        
    def cities_match(city1, city2):
        return city1.lower().strip() == city2.lower().strip()
        
    def normalize_city(city):
        return city.lower().strip() if city else ""
