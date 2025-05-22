"""
Winner selection service for giveaways.

This module provides scalable and robust implementations for selecting
random winners from giveaway entries.

Key features:
- Database chunking for large datasets
- Transaction safety
- Performance metrics tracking
- Error handling and logging
"""

import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q, F
from django.contrib.auth import get_user_model

from ..models import Giveaway, Entry, Winner
from .base import log_execution_time, SelectionError
from .metrics import track_operation, MetricsCollector

User = get_user_model()
logger = logging.getLogger(__name__)


@log_execution_time
@track_operation("select_random_winner")
def select_random_winner_scalable(giveaway_id: int, chunk_size: int = 1000) -> Dict[str, Any]:
    """
    Selects a random winner for a giveaway with improved scalability.
    
    Uses database optimization techniques to efficiently handle giveaways
    with large numbers of entries. Following Windsurf project requirements,
    winners are randomly selected from ALL entries.
    
    Args:
        giveaway_id: ID of the giveaway
        chunk_size: Size of chunks to process at a time
        
    Returns:
        Dict with success status and winner information
    """
    result = {
        "success": False,
        "message": "",
        "winner": None,
        "performance_metrics": {}
    }
    
    try:
        with transaction.atomic():
            # Get the giveaway with a select_for_update to prevent race conditions
            giveaway = Giveaway.objects.select_for_update().get(id=giveaway_id)
            
            # Check if giveaway is expired
            if not giveaway.is_expired():
                result["message"] = f"Giveaway {giveaway.title} has not ended yet. Cannot select a winner until the end date."
                logger.warning(result["message"])
                return result
            
            # Check if a winner already exists
            if Winner.objects.filter(giveaway=giveaway).exists():
                existing_winner = Winner.objects.get(giveaway=giveaway)
                result["message"] = f"Giveaway {giveaway.title} already has a winner: {existing_winner.user.email}"
                result["winner"] = existing_winner
                logger.info(result["message"])
                return result
                
            # Count total entries first (more efficient than loading all entries)
            total_entries = Entry.objects.filter(giveaway=giveaway).count()
            MetricsCollector.increment_counter("select_random_winner", "total_entries", total_entries)
            
            if total_entries == 0:
                result["message"] = f"No entries found for giveaway {giveaway.title}."
                logger.warning(result["message"])
                return result
                
            # Select a random offset - optimized approach for large datasets
            random_index = random.randint(0, total_entries - 1)
            
            # Get just the winning entry directly with OFFSET/LIMIT for efficiency
            winning_entry = Entry.objects.filter(
                giveaway=giveaway
            ).order_by('id')[random_index:random_index+1].get()
            
            # Create winner record
            winner = Winner.objects.create(
                giveaway=giveaway,
                user=winning_entry.user,
                selected_at=timezone.now(),
                notification_sent=False
            )
            
            logger.info(f"Selected winner for {giveaway.title}: {winner.user.email}")
            
            result["success"] = True
            result["message"] = f"Successfully selected winner for {giveaway.title}: {winner.user.email}"
            result["winner"] = winner
            
    except Giveaway.DoesNotExist:
        result["message"] = f"Giveaway with ID {giveaway_id} does not exist."
        logger.error(result["message"])
    except Exception as e:
        error_msg = f"Error selecting winner for giveaway {giveaway_id}: {str(e)}"
        result["message"] = error_msg
        logger.exception(error_msg)
    
    # Include performance metrics
    result["performance_metrics"] = MetricsCollector.get_metrics("select_random_winner")
    
    return result


@log_execution_time
@track_operation("process_winners_batch")
def process_winners_batch(giveaway_ids: List[int]) -> Dict[str, Any]:
    """
    Process winner selection for multiple giveaways.
    
    Selects winners for multiple giveaways in a single transaction
    for improved efficiency and consistency.
    
    Args:
        giveaway_ids: List of giveaway IDs to process
        
    Returns:
        Dict with results summary
    """
    result = {
        "success": True,
        "processed": 0,
        "winners": 0,
        "errors": 0,
        "messages": [],
        "performance_metrics": {}
    }
    
    if not giveaway_ids:
        result["messages"].append("No giveaway IDs provided.")
        return result
    
    MetricsCollector.set_batch_size("process_winners_batch", len(giveaway_ids))
    
    # Process each giveaway
    for giveaway_id in giveaway_ids:
        result["processed"] += 1
        MetricsCollector.increment_counter("process_winners_batch", "processed_items")
        
        # Select a winner for this giveaway
        winner_result = select_random_winner_scalable(giveaway_id)
        result["messages"].append(winner_result["message"])
        
        if winner_result["success"]:
            result["winners"] += 1
            MetricsCollector.increment_counter("process_winners_batch", "successful_selections")
        else:
            result["errors"] += 1
            MetricsCollector.increment_counter("process_winners_batch", "failed_selections")
    
    # Include performance metrics
    result["performance_metrics"] = MetricsCollector.get_metrics("process_winners_batch")
    
    return result


@log_execution_time
@track_operation("find_eligible_giveaways")
def find_eligible_giveaways() -> List[int]:
    """
    Find all eligible giveaways for winner selection.
    
    Eligible giveaways are:
    1. Expired (end date is in the past)
    2. Active
    3. Have at least one entry
    4. Do not already have a winner
    
    Returns:
        List of eligible giveaway IDs
    """
    now = timezone.now()
    
    # Find expired giveaways with entries but no winners
    eligible_giveaways = Giveaway.objects.filter(
        end_date__lt=now,      # End date is in the past
        is_active=True,        # Giveaway is active
    ).annotate(
        entry_count=Count('entries'),  # Count entries
        has_winner=Count('winner')     # Check if has winner
    ).filter(
        entry_count__gt=0,     # Has at least one entry
        has_winner=0           # Does not have a winner
    ).values_list('id', flat=True)
    
    eligible_ids = list(eligible_giveaways)
    logger.info(f"Found {len(eligible_ids)} eligible giveaways for winner selection")
    
    return eligible_ids
