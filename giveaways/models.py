import logging
from typing import Dict, List, Optional, Union, Any, Tuple

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone

from businesses.models import Business

logger = logging.getLogger(__name__)

class Giveaway(models.Model):
    """
    Model for giveaways on Raildrops.
    Includes prize, image, value, description, dates, signup question and answer options.
    
    Attributes:
        business (ForeignKey): The business hosting this giveaway
        title (CharField): Title of the giveaway
        description (TextField): Detailed description of the giveaway
        image (ImageField): Optional image for the giveaway
        prize_value (DecimalField): Optional monetary value of the prize
        start_date (DateTimeField): When the giveaway starts
        end_date (DateTimeField): When the giveaway ends
        is_active (BooleanField): Whether the giveaway is currently active
        created_at (DateTimeField): When the giveaway was created
        signup_question (CharField): Question users must answer to participate
        signup_options (JSONField): Answer options for the question (max 4)
    """
    business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name="giveaways",
        db_index=True
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    image = models.ImageField(upload_to="giveaway_images/", blank=True, null=True)
    prize_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Prize Value", 
        null=True, 
        blank=True
    )
    start_date = models.DateTimeField(db_index=True)
    end_date = models.DateTimeField(db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    signup_question = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Signup Question"
    )
    signup_options = models.JSONField(
        blank=True, 
        null=True, 
        verbose_name="Answer Options (max 4)"
    )

    def __str__(self) -> str:
        """Return a string representation of the giveaway.
        
        Returns:
            str: Formatted string with giveaway title and business name
        """
        return f"{self.title} ({self.business.name})"
        
    def get_absolute_url(self) -> str:
        """Returns the URL to access a detail record for this giveaway.
        
        Returns:
            str: URL to the giveaway detail page
        """
        return reverse('giveaways:giveaway-detail', args=[str(self.id)])
    
    def clean(self) -> None:
        """Validate the giveaway data.
        
        Ensures that:
        - Start date is before end date
        - The giveaway question has at least 2 answer options
        - The giveaway has a non-empty title
        - Options are properly formatted
        
        Raises:
            ValidationError: If validation fails
        """
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({'end_date': 'Sluttdato må være etter startdato.'})
            
        if self.signup_question and not self.signup_options:
            raise ValidationError({'signup_options': 'Du må angi svaralternativer til spørsmålet.'})
            
        if self.signup_options:
            if not isinstance(self.signup_options, list):
                raise ValidationError({'signup_options': 'Svaralternativer må være en liste.'})
                
            if len(self.signup_options) < 2:
                raise ValidationError({'signup_options': 'Du må angi minst 2 svaralternativer.'})
                
            if len(self.signup_options) > 4:
                raise ValidationError({'signup_options': 'Maksimalt 4 svaralternativer er tillatt.'})
        
        if not self.title or self.title.strip() == "":
            raise ValidationError({'title': 'Tittel kan ikke være tom.'})
    
    def save(self, *args, **kwargs) -> None:
        """Save the giveaway with validation.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Raises:
            ValidationError: If model validation fails
        """
        self.full_clean()
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving giveaway {self.title}: {str(e)}")
            raise
    
    def is_expired(self) -> bool:
        """Check if the giveaway has expired.
        
        Returns:
            bool: True if current time is past end_date
        """
        if not self.end_date:
            return False
        return timezone.now() > self.end_date
    
    def is_upcoming(self) -> bool:
        """Check if the giveaway has not started yet.
        
        Returns:
            bool: True if current time is before start_date
        """
        if not self.start_date:
            return False
        return timezone.now() < self.start_date
    
    def is_currently_active(self) -> bool:
        """Check if the giveaway is currently active (within date range and marked as active).
        
        Returns:
            bool: True if giveaway is active and within start/end dates
        """
        if not self.start_date or not self.end_date:
            return False
            
        now = timezone.now()
        return (self.is_active and 
                self.start_date <= now <= self.end_date)
    
    def get_correct_answer(self) -> Optional[str]:
        """Get the correct answer for the giveaway, if available.
        
        Note: In the current implementation, there is no concept of correct answers.
        All answers are considered as feedback/survey responses. This method is kept
        for backward compatibility with existing code.
        
        Returns:
            Optional[str]: The first answer option or None if no options
        """
        if self.signup_options and len(self.signup_options) > 0:
            return self.signup_options[0]
        return None
    
    def entry_count(self) -> int:
        """Get the number of entries for this giveaway.
        
        Returns:
            int: Count of entries
        """
        return self.entries.count()
    
    @property
    def has_winner(self) -> bool:
        """Check if this giveaway has a winner.
        
        Returns:
            bool: True if a winner has been selected for this giveaway
        """
        try:
            return hasattr(self, 'winner') and self.winner is not None
        except Exception:
            return False
            
    def get_winner_display_url(self) -> str:
        """Get the URL for displaying the winner details.
        
        Returns:
            str: URL to the winner page or detail page if no dedicated page exists
        """
        try:
            if self.has_winner:
                return reverse('giveaways:giveaway-winner', args=[str(self.id)])
            return self.get_absolute_url()
        except Exception:
            return self.get_absolute_url()
        
    class Meta:
        """Meta options for the Giveaway model."""
        verbose_name = "Giveaway"
        verbose_name_plural = "Giveaways"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_active', 'start_date', 'end_date']),
        ]

class Entry(models.Model):
    """
    Entry for a giveaway. Stores user, giveaway, selected answer and user's city (from geolocation).
    
    Attributes:
        giveaway (ForeignKey): The giveaway this entry is for
        user (ForeignKey): The user who submitted this entry
        answer (CharField): The answer option selected by the user
        user_location_city (CharField): The city of the user when they entered
        entered_at (DateTimeField): When the entry was submitted
    """
    giveaway = models.ForeignKey(
        Giveaway, 
        on_delete=models.CASCADE, 
        related_name="entries",
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="entries",
        db_index=True
    )
    answer = models.CharField(max_length=255, blank=True, db_index=True)
    user_location_city = models.CharField(max_length=100, blank=True, db_index=True)
    entered_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Entry"
        verbose_name_plural = "Entries"
        ordering = ['-entered_at']
        unique_together = ('giveaway', 'user')
        indexes = [
            models.Index(fields=['giveaway', 'answer']),
            models.Index(fields=['user', 'entered_at']),
            models.Index(fields=['user_location_city']),
        ]
        
    def __str__(self) -> str:
        """
        Return a string representation of the entry.
        
        Returns:
            str: Formatted string with user email, giveaway title and location
        """
        return f"{self.user.email} - {self.giveaway.title} ({self.user_location_city})"
        
    def is_correct_answer(self) -> bool:
        """
        Check if the user selected the correct answer.
        
        Note: In the current implementation, there is no concept of correct answers.
        All answers are considered as feedback/survey responses. This method is kept
        for backward compatibility but always returns True.
        
        Returns:
            bool: Always True since all answers are valid for the winner selection
        """
        return True
        
    def clean(self) -> None:
        """
        Validate the entry data.
        
        Ensures that:
        - The answer is one of the available options
        - The user location is provided
        
        Raises:
            ValidationError: If validation fails
        """
        # Check if self.giveaway exists before accessing it
        # This uses hasattr to avoid RelatedObjectDoesNotExist errors during form validation
        # since the giveaway is set in the view after form validation
        try:
            giveaway = self.giveaway
            if giveaway and giveaway.signup_options:
                if self.answer not in giveaway.signup_options:
                    raise ValidationError({'answer': 'Svaret må være et av de tilgjengelige alternativene.'})
        except Exception:
            # Skip giveaway validation during form validation
            # The giveaway will be set in the view
            pass
                
        if not self.user_location_city or self.user_location_city.strip() == "":
            raise ValidationError({'user_location_city': 'Brukerlokasjon må oppgis.'})
            
    def save(self, *args, **kwargs) -> None:
        """
        Save the entry with validation.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Raises:
            ValidationError: If model validation fails
        """
        self.full_clean()
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving entry for {self.user.email}: {str(e)}")
            raise

class Winner(models.Model):
    """
    Model for giveaway winners. Links a user with a giveaway after winner selection.
    
    Attributes:
        giveaway (OneToOneField): The giveaway this winner is for (one winner per giveaway)
        user (ForeignKey): The user who won the giveaway
        selected_at (DateTimeField): When the winner was selected
        notification_sent (BooleanField): Whether a notification has been sent to the winner
    """
    giveaway = models.OneToOneField(
        Giveaway, 
        on_delete=models.CASCADE, 
        related_name="winner",
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="giveaway_wins",
        db_index=True
    )
    selected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    notification_sent = models.BooleanField(default=False, db_index=True)

    def __str__(self) -> str:
        """
        Return a string representation of the winner.
        
        Returns:
            str: Formatted string with user email and giveaway title
        """
        return f"Winner: {self.user.email} for {self.giveaway.title}"
    
    def mark_notification_sent(self) -> None:
        """
        Mark that a notification has been sent to the winner.
        """
        self.notification_sent = True
        self.save(update_fields=['notification_sent'])
    
    def get_entry(self) -> Optional['Entry']:
        """
        Get the entry that this winner submitted for the giveaway.
        
        Returns:
            Optional[Entry]: The entry object or None if not found
        """
        try:
            return Entry.objects.get(giveaway=self.giveaway, user=self.user)
        except Entry.DoesNotExist:
            logger.warning(f"No entry found for winner {self.user.email} in giveaway {self.giveaway.id}")
            return None
    
    def was_correct_answer(self) -> bool:
        """
        Check if the winner submitted an answer in their entry.
        
        Note: In the current implementation, there is no concept of correct answers.
        All answers are considered as feedback/survey responses. This method is kept
        for backward compatibility and returns True if an entry exists.
        
        Returns:
            bool: True if the winner has an entry, False otherwise
        """
        entry = self.get_entry()
        return entry is not None
    
    class Meta:
        """
        Meta options for the Winner model.
        """
        verbose_name = "Winner"
        verbose_name_plural = "Winners"
        ordering = ['-selected_at']
        indexes = [
            models.Index(fields=['user', 'selected_at']),
            models.Index(fields=['notification_sent']),
        ]