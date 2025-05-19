"""
Business logic for giveaways. This module contains all logic for city matching, validation, and winner selection.
"""
import unicodedata
import logging
logger = logging.getLogger(__name__)

def normalize_city(city: str) -> str:
    if not city:
        return ""
    city = city.lower().strip()
    city = unicodedata.normalize('NFKD', city)
    city = ''.join(c for c in city if c.isalnum())
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
    if not cities_match(user_city, giveaway.business.city):
        # Create a more informative error message
        return {
            "success": False, 
            "error": f"You must be in {giveaway.business.city} to participate in this giveaway. Your current position is registered as {user_city}."
        }
    
    # Log successful location match
    logger.info(f"Approved position: {user_city} matches {giveaway.business.city}")
    
    return {"success": True, "normalized_city": normalize_city(user_city)}
