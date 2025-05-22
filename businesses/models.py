import logging
from typing import Dict, List, Optional, Tuple, Union

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class Business(models.Model):
    """
    Model for business profile on Raildrops.
    Contains information about the business, admin, and associated user.
    Follows PEP8, uses meaningful comments, and robust validation.
    
    Attributes:
        user (OneToOneField): The user account associated with this business
        admin (ForeignKey): The user who administers this business
        organization_number (CharField): Unique organization identifier
        name (CharField): The business name
        description (TextField): Detailed description of the business
        logo (ImageField): Business logo image
        website (URLField): Business website
        postal_code (CharField): Postal code of business location
        city (CharField): City of business location
        address (CharField): Street address of the business
        phone (CharField): Contact phone number
        contact_person (CharField): Name of primary contact person
        social_media (JSONField): Links to social media platforms
        created_at (DateTimeField): When the business profile was created
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="business_account",
        db_index=True
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="admin_businesses", 
        help_text="User who is the admin for this business",
        db_index=True
    )
    organization_number = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True, 
        help_text="Organization number must be unique",
        db_index=True
    )
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="business_logos/", blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, db_index=True)
    city = models.CharField(max_length=64, blank=True, db_index=True)
    address = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Address", 
        help_text="Street address of the business"
    )
    phone = models.CharField(
        max_length=32, 
        blank=True, 
        null=True, 
        verbose_name="Phone", 
        help_text="Contact phone for the business"
    )
    contact_person = models.CharField(
        max_length=128, 
        blank=True, 
        null=True, 
        verbose_name="Contact Person", 
        help_text="Name of the main contact for the business"
    )
    social_media = models.JSONField(
        blank=True, 
        null=True, 
        verbose_name="Social Media", 
        help_text="Links to Facebook, Instagram, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self) -> str:
        """
        Returns the name, city, and admin email for the business.
        
        Returns:
            str: Formatted string with business name, city and admin email
        """
        return f"{self.name} ({self.city or 'Ingen by'}) - Admin: {self.admin.email if self.admin else 'Ingen'}"

    def clean(self) -> None:
        """
        Extra validation for the Business model.
        Checks that the name is not empty and that the postal code contains only digits.
        
        Raises:
            ValidationError: If validation fails
        """
        if not self.name or self.name.strip() == "":
            raise ValidationError({"name": "Bedriftsnavn kan ikke være tomt."})
        
        if self.postal_code:
            if not self.postal_code.isdigit():
                raise ValidationError({"postal_code": "Postnummer kan kun inneholde sifre."})
            if len(self.postal_code) not in [4, 5]:
                raise ValidationError({"postal_code": "Postnummer må være 4 eller 5 sifre."})
                
        if self.phone and not self.phone.replace('+', '').replace(' ', '').isdigit():
            raise ValidationError({"phone": "Telefonnummer kan kun inneholde sifre, + og mellomrom."})
            
        if self.website and not self.website.startswith(('http://', 'https://')):
            raise ValidationError({"website": "Nettside må starte med http:// eller https://"})

    def save(self, *args, **kwargs) -> None:
        """
        Saves the Business object with validation and robust error handling.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            
        Raises:
            ValidationError: If model validation fails
            Exception: If database save fails
        """
        self.full_clean()
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving business {self.name}: {str(e)}")
            raise
            
    def get_display_address(self) -> str:
        """
        Returns a formatted complete address.
        
        Returns:
            str: Comma-separated address components (address, postal_code, city)
        """
        parts = filter(None, [self.address, self.postal_code, self.city])
        return ", ".join(parts)
        
    def get_social_links(self) -> List[Tuple[str, str]]:
        """
        Returns social media as a list of name/url pairs.
        
        Returns:
            List[Tuple[str, str]]: List of tuples containing (platform_name, url)
        """
        if not self.social_media:
            return []
        try:
            return [(k, v) for k, v in self.social_media.items()]
        except (TypeError, AttributeError) as e:
            logger.warning(f"Invalid social_media format for business {self.pk}: {e}")
            return []
            
    def has_complete_profile(self) -> bool:
        """
        Checks if the business profile has all recommended fields filled out.
        
        Returns:
            bool: True if all recommended fields are filled, False otherwise
        """
        required_fields = ['name', 'description', 'city', 'phone', 'contact_person']
        return all(bool(getattr(self, field)) for field in required_fields)
        
    class Meta:
        """
        Meta options for the Business model.
        """
        verbose_name = "Bedrift"
        verbose_name_plural = "Bedrifter"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name', 'city']),
            models.Index(fields=['created_at']),
            models.Index(fields=['admin'])
        ]