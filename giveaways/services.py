"""
Business logic for giveaways. This module contains all logic for city matching, validation, and winner selection.
"""
import unicodedata
import logging
import random
from typing import Optional, Tuple, Dict, Any, List
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q

# Get the models here to avoid circular imports
from .models import Giveaway, Entry, Winner

User = get_user_model()
logger = logging.getLogger(__name__)

def normalize_city(city: str) -> str:
    """Normalize city name for consistent comparison.
    
    Removes accents, spaces, case sensitivity, and special characters.
    
    Args:
        city: The city name to normalize
        
    Returns:
        Normalized city name for comparison
    """
    if not city:
        return ""
    city = city.lower().strip()
    city = unicodedata.normalize('NFKD', city)
    # Remove all non-alphanumeric characters
    city = ''.join(c for c in city if c.isalnum())
    # Log the normalization for debugging
    logger.debug(f"Normalized city: '{city}'")
    return city

def cities_match(user_city: str, giveaway_city: str) -> bool:
    """Return True if cities match (robust, accent/space/case insensitive)."""
    return normalize_city(user_city) == normalize_city(giveaway_city)

def validate_entry(user, giveaway, user_city: str, answer: str) -> dict:
    """Validates entry submission. Returns dict with 'success', 'error' and optionally 'normalized_city'."""
    # Always require an answer
    if not answer:
        return {"success": False, "error": "You must select an answer."}
    
    # Always require a city location
    if not user_city:
        return {"success": False, "error": "Your location must be registered. Allow location sharing or enter city manually."}
    
    # IMPORTANT: Users must be in the same city as the business to participate
    # This is a vital function for Raildrops
    normalized_user_city = normalize_city(user_city)
    normalized_business_city = normalize_city(giveaway.business.city)
    
    # Log the normalization for debugging
    logger.info(f"Comparing user city '{user_city}' ({normalized_user_city}) with business city '{giveaway.business.city}' ({normalized_business_city})")
    
    if not normalized_user_city:
        # Edge case: Empty normalized city
        return {"success": False, "error": f"Invalid city format: {user_city}. Please update your profile with a valid city."}
    
    if normalized_user_city != normalized_business_city:
        # Create a more informative error message
        return {
            "success": False, 
            "error": f"You must be in {giveaway.business.city} to participate in this giveaway. Your current position is registered as {user_city}."
        }
    
    # Log successful location match
    logger.info(f"Approved position: {user_city} matches {giveaway.business.city}")
    
    return {"success": True, "normalized_city": normalized_user_city}


def select_random_winner(giveaway_id: int) -> Dict[str, Any]:
    """
    Selects a random winner for a giveaway from all participants.
    
    This function follows the Windsurf project requirements by:
    1. Selecting randomly from all giveaway entries
    2. Using a truly random selection
    3. Creating a Winner record
    4. Setting notification status
    
    Args:
        giveaway_id (int): The ID of the giveaway to select a winner for
        
    Returns:
        Dict containing success status, winner info if successful, and error message if not
    """
    result = {
        "success": False,
        "message": "",
        "winner": None
    }
    
    try:
        # Get the giveaway
        giveaway = Giveaway.objects.get(id=giveaway_id)
        
        # Check if giveaway is expired
        if not giveaway.is_expired():
            result["message"] = f"Giveaway {giveaway.title} has not ended yet. Cannot select a winner until the end date."
            logger.warning(result["message"])
            return result
        
        # Check if a winner already exists
        try:
            existing_winner = Winner.objects.get(giveaway=giveaway)
            result["message"] = f"Giveaway {giveaway.title} already has a winner: {existing_winner.user.email}"
            result["winner"] = existing_winner
            logger.info(result["message"])
            return result
        except Winner.DoesNotExist:
            pass  # This is expected, we can proceed
        
        # Get all entries for the giveaway (no filtering by correct answer)
        entries = Entry.objects.filter(giveaway=giveaway)
        
        if not entries.exists():
            result["message"] = f"No entries found for giveaway {giveaway.title}."
            logger.warning(result["message"])
            return result
        
        # Convert to list for random selection
        entries_list = list(entries)
        
        # Select a random entry with the correct answer
        winning_entry = random.choice(entries_list)
        
        # Create the winner record in a transaction to ensure data integrity
        with transaction.atomic():
            winner = Winner.objects.create(
                giveaway=giveaway,
                user=winning_entry.user,
                selected_at=timezone.now(),
                notification_sent=False
            )
            
            # Log the winner selection
            logger.info(f"Selected winner for {giveaway.title}: {winner.user.email}")
            
            result["success"] = True
            result["message"] = f"Successfully selected winner for {giveaway.title}: {winner.user.email}"
            result["winner"] = winner
            
            return result
            
    except Giveaway.DoesNotExist:
        result["message"] = f"Giveaway with ID {giveaway_id} does not exist."
        logger.error(result["message"])
    except Exception as e:
        result["message"] = f"Error selecting winner: {str(e)}"
        logger.exception(f"Unexpected error selecting winner for giveaway {giveaway_id}: {str(e)}")
    
    return result


def can_select_winners_for_expired_giveaways() -> Dict[str, Any]:
    """
    Find all expired giveaways without winners and select winners for them.
    
    Returns:
        Dict with results information
    """
    result = {
        "success": True,
        "processed": 0,
        "winners": 0,
        "errors": 0,
        "messages": []
    }
    
    # Find expired giveaways without winners
    now = timezone.now()
    expired_giveaways = Giveaway.objects.filter(
        end_date__lt=now,  # End date is in the past
        is_active=True     # Giveaway is active
    ).exclude(
        winner__isnull=False  # No winner yet
    )
    
    if not expired_giveaways.exists():
        result["messages"].append("No expired giveaways without winners found.")
        return result
    
    # Process each expired giveaway
    for giveaway in expired_giveaways:
        result["processed"] += 1
        
        # Select a winner
        winner_result = select_random_winner(giveaway.id)
        result["messages"].append(winner_result["message"])
        
        if winner_result["success"]:
            result["winners"] += 1
        else:
            result["errors"] += 1
    
    return result
