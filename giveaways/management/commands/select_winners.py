"""
Management command to select winners for expired giveaways.
This can be run manually or scheduled with Celery.
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from giveaways.services import can_select_winners_for_expired_giveaways

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Selects winners randomly from all entries for expired giveaways that do not already have winners.'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Show what would happen without making actual changes',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS(f'Starting winner selection process at {timezone.now()}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No database changes will be made'))
        
        try:
            # Call the service function to handle the winner selection logic
            results = can_select_winners_for_expired_giveaways() if not dry_run else {
                'success': True,
                'processed': 0,
                'winners': 0,
                'errors': 0,
                'messages': ['Dry run mode - no action taken']
            }
            
            # Output results
            self.stdout.write(self.style.SUCCESS(
                f'Winner selection completed: '
                f'Processed {results["processed"]} giveaways, '
                f'Selected {results["winners"]} winners, '
                f'Encountered {results["errors"]} errors'
            ))
            
            for message in results['messages']:
                self.stdout.write(message)
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error in winner selection process: {str(e)}'))
            logger.exception('Error in select_winners management command')
            raise
            
        self.stdout.write(self.style.SUCCESS(f'Winner selection process completed at {timezone.now()}'))
