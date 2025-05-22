"""
Test script for the winner selection functionality.
This script can be run directly from the Django shell to test the winner selection process.
"""

import os
import sys
import django
import logging
from django.utils import timezone
from django.db import transaction

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up Django environment
def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'raildrops.settings')
    django.setup()

def test_winner_selection():
    """
    Test the winner selection process on existing giveaways.
    """
    from giveaways.services.winner_selection import find_eligible_giveaways, process_winners_batch, select_random_winner_scalable
    from giveaways.models import Giveaway, Entry, Winner
    
    # Find all eligible giveaways
    eligible_giveaways = find_eligible_giveaways()
    logger.info(f"Found {len(eligible_giveaways)} eligible giveaways for testing")
    
    if not eligible_giveaways:
        logger.warning("No eligible giveaways found for testing. Creating a test case...")
        
        # Create a test giveaway if none exists
        try:
            with transaction.atomic():
                # Find any active giveaway without a winner that has entries
                test_giveaways = Giveaway.objects.filter(is_active=True).exclude(
                    id__in=Winner.objects.values_list('giveaway_id', flat=True)
                ).annotate(entry_count=django.db.models.Count('entries')).filter(entry_count__gt=0)
                
                if test_giveaways.exists():
                    # Force one to be "expired" temporarily for testing
                    test_giveaway = test_giveaways.first()
                    original_end_date = test_giveaway.end_date
                    
                    # Temporarily set end date to the past
                    test_giveaway.end_date = timezone.now() - timezone.timedelta(days=1)
                    test_giveaway.save(update_fields=['end_date'])
                    
                    logger.info(f"Temporarily set giveaway {test_giveaway.id} as expired for testing")
                    
                    # Add to eligible list
                    eligible_giveaways = [test_giveaway.id]
                    
                    try:
                        # Test winner selection
                        logger.info("Testing winner selection on single giveaway...")
                        result = select_random_winner_scalable(test_giveaway.id)
                        logger.info(f"Selection result: {result}")
                        
                        # Restore original end date
                        test_giveaway.end_date = original_end_date
                        test_giveaway.save(update_fields=['end_date'])
                        
                        # If we created a winner, delete it since this was just a test
                        if result.get('success', False) and result.get('winner'):
                            result['winner'].delete()
                            logger.info("Cleaned up test winner")
                            
                        return result
                    except Exception as e:
                        # Restore original end date
                        test_giveaway.end_date = original_end_date
                        test_giveaway.save(update_fields=['end_date'])
                        raise e
                else:
                    logger.error("No suitable giveaways found for testing")
                    return {"success": False, "message": "No suitable giveaways found for testing"}
        except Exception as e:
            logger.exception(f"Error in test setup: {str(e)}")
            return {"success": False, "error": str(e)}
    else:
        # Test the batch process with real eligible giveaways
        logger.info(f"Testing batch winner selection on {len(eligible_giveaways)} giveaways...")
        result = process_winners_batch(eligible_giveaways)
        logger.info(f"Batch selection results: {result}")
        return result
    
if __name__ == "__main__":
    setup_django()
    test_winner_selection()
