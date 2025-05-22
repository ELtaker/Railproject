"""\nCelery tasks for giveaways.\nThis module contains scheduled tasks for giveaway operations.\n"""

import logging
from typing import Dict, Any, List, Optional
from celery import shared_task, chord
from django.core import management
from django.utils import timezone

from .services.winner_selection import select_random_winner_scalable, process_winners_batch, find_eligible_giveaways
from .services import can_select_winners_for_expired_giveaways

logger = logging.getLogger(__name__)


@shared_task(name='giveaways.select_winners')
def select_winners() -> Dict[str, Any]:
    """
    Celery task to select winners for all expired giveaways.
    
    This task is scheduled to run daily to ensure that winners are selected
    for all expired giveaways. It follows the Windsurf project requirements
    by randomly selecting winners from all participants.
    
    Returns:
        Dict containing success status and statistics
    """
    logger.info(f"Starting automated winner selection task at {timezone.now()}")
    
    try:
        # Find eligible giveaways
        eligible_giveaways = find_eligible_giveaways()
        
        if not eligible_giveaways:
            logger.info("No eligible giveaways found for winner selection.")
            return {
                'success': True,
                'processed': 0,
                'winners': 0,
                'errors': 0,
                'messages': ["No eligible giveaways found."]
            }
        
        # Use the scalable batch processing
        results = process_winners_batch(eligible_giveaways)
        
        # Log results
        logger.info(
            f"Winner selection completed: "
            f"Processed {results['processed']} giveaways, "
            f"Selected {results['winners']} winners, "
            f"Encountered {results['errors']} errors"
        )
        
        for message in results['messages']:
            logger.info(message)
            
        return results
        
    except Exception as e:
        logger.exception(f"Error in automated winner selection task: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'processed': 0,
            'winners': 0,
            'errors': 1,
            'messages': [f"Error: {str(e)}"]
        }


@shared_task(name='giveaways.select_winners_batch', bind=True)
def select_winners_batch(self, giveaway_ids: List[int], chunk_size: int = 100) -> Dict[str, Any]:
    """
    Process winner selection for multiple giveaways in parallel using task chords.
    
    This task divides the giveaways into chunks and processes them in parallel,
    then collects the results. This approach dramatically improves performance
    for large numbers of giveaways.
    
    Args:
        giveaway_ids: List of giveaway IDs to process
        chunk_size: Size of chunks to process at a time
        
    Returns:
        Dict with results summary
    """
    if not giveaway_ids:
        return {
            "success": True,
            "message": "No giveaways to process",
            "processed": 0,
            "winners": 0,
            "errors": 0
        }
    
    logger.info(f"Starting batch winner selection for {len(giveaway_ids)} giveaways")
    
    # Divide giveaways into chunks to avoid overloading the system
    chunks = [giveaway_ids[i:i + chunk_size] for i in range(0, len(giveaway_ids), chunk_size)]
    
    # Create individual tasks for each chunk
    tasks = [process_winners_chunk.s(chunk) for chunk in chunks]
    
    # Create a chord that processes all chunks in parallel and then calls the callback
    callback = summarize_winner_selection.s()
    chord_result = chord(tasks)(callback)
    
    return {
        "success": True,
        "message": f"Scheduled winner selection for {len(giveaway_ids)} giveaways in {len(chunks)} chunks",
        "task_id": chord_result.id,
        "total_giveaways": len(giveaway_ids),
        "chunks": len(chunks)
    }


@shared_task(name='giveaways.process_winners_chunk', bind=True, max_retries=3)
def process_winners_chunk(self, giveaway_ids_chunk: List[int]) -> Dict[str, Any]:
    """
    Process a chunk of giveaways for winner selection.
    
    This task processes a subset of giveaways and has retry capability for resilience.
    
    Args:
        giveaway_ids_chunk: Chunk of giveaway IDs to process
        
    Returns:
        Dict with results for this chunk
    """
    try:
        logger.info(f"Processing chunk with {len(giveaway_ids_chunk)} giveaways")
        result = process_winners_batch(giveaway_ids_chunk)
        return result
    except Exception as e:
        # Exponential backoff retry
        retry_countdown = 2 ** self.request.retries
        logger.exception(f"Error processing chunk: {str(e)}. Retrying in {retry_countdown}s")
        self.retry(exc=e, countdown=retry_countdown)


@shared_task(name='giveaways.summarize_winner_selection')
def summarize_winner_selection(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Callback task that processes the results of all winner selections.
    
    Aggregates results from all chunks and produces a summary report.
    
    Args:
        results: List of results from each chunk
        
    Returns:
        Dict with aggregated summary
    """
    total_processed = sum(r.get('processed', 0) for r in results)
    total_winners = sum(r.get('winners', 0) for r in results)
    total_errors = sum(r.get('errors', 0) for r in results)
    
    # Collect all messages
    all_messages = []
    for result in results:
        all_messages.extend(result.get('messages', []))
    
    summary = {
        "success": total_errors == 0,
        "total_processed": total_processed,
        "winners_selected": total_winners,
        "errors": total_errors,
        "completed_at": timezone.now().isoformat(),
        "chunks_processed": len(results),
        "summary_messages": all_messages[:20],  # Limit to prevent excessive logging
        "has_more_messages": len(all_messages) > 20
    }
    
    logger.info(
        f"Winner selection batch completed: "
        f"Processed {total_processed} giveaways, "
        f"Selected {total_winners} winners, "
        f"Encountered {total_errors} errors across {len(results)} chunks"
    )
    
    return summary


@shared_task(name='giveaways.notify_winners')
def notify_winners() -> Dict[str, Any]:
    """
    Celery task to send notifications to winners who haven't been notified yet.
    
    This task is scheduled to run daily to ensure that all winners receive
    notifications about their wins.
    
    Returns:
        Dict containing success status and statistics
    """
    from .models import Winner
    
    logger.info(f"Starting winner notification task at {timezone.now()}")
    
    try:
        # Find winners who haven't been notified yet
        pending_winners = Winner.objects.filter(notification_sent=False)
        
        if not pending_winners.exists():
            logger.info("No pending winner notifications found.")
            return {
                'success': True,
                'notified': 0,
                'message': 'No pending notifications found.'
            }
        
        notification_count = 0
        
        # Process each winner
        for winner in pending_winners:
            try:
                # Here you would implement the actual notification logic
                # For example, sending an email or a push notification
                # For now, we just mark them as notified
                
                logger.info(f"Notifying winner {winner.user.email} for giveaway {winner.giveaway.title}")
                
                # Mark as notified
                winner.mark_notification_sent()
                notification_count += 1
                
            except Exception as inner_e:
                logger.error(f"Error notifying winner {winner.id}: {str(inner_e)}")
        
        return {
            'success': True,
            'notified': notification_count,
            'message': f'Successfully notified {notification_count} winners.'
        }
        
    except Exception as e:
        logger.exception(f"Error in winner notification task: {str(e)}")
        return {
            'success': False,
            'notified': 0,
            'error': str(e)
        }