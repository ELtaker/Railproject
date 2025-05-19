"""
Forretningslogikk for giveaways. Her samles all logikk for by-match, validering og vinner-trekning.
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
    """Validerer påmelding. Returnerer dict med 'success', 'error' og evt. 'normalized_city'."""
    # Always require an answer
    if not answer:
        return {"success": False, "error": "Du må velge et svar."}
    
    # Always require a city location
    if not user_city:
        return {"success": False, "error": "Din lokasjon må registreres. Tillat posisjonsdeling eller oppgi by manuelt."}
    
    # IMPORTANT: Users must be in the same city as the business to participate
    # This is a vital function for Raildrops
    if not cities_match(user_city, giveaway.business.city):
        # Create a more informative error message
        return {
            "success": False, 
            "error": f"Du må være i {giveaway.business.city} for å delta i denne giveawayen. Din nåværende posisjon er registrert som {user_city}."
        }
    
    # Log successful location match
    logger.info(f"Godkjent posisjon: {user_city} matcher {giveaway.business.city}")
    
    return {"success": True, "normalized_city": normalize_city(user_city)}
