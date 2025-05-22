from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):
    """
    Custom user model for Raildrops.
    Uses email as the primary login identifier and enforces unique, lowercase emails.
    Includes profile image and city fields.
    """
    email = models.EmailField(
        _('email address'), 
        unique=True, 
        db_index=True,  # Add index for better performance
        help_text="Unique email address for login."
    )
    profile_image = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Profile image for the user."
    )
    city = models.CharField(
        max_length=100, 
        blank=True, 
        db_index=True,  # Add index for location-based filtering
        help_text="User's city/location."
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username is still required for admin compatibility

    def __str__(self) -> str:
        return self.email or self.username

    def clean(self) -> None:
        """
        Validate the model fields before saving.
        
        Performs custom validation on city and email fields:
        - Ensures city name doesn't contain numbers
        - Validates email format using Django's EmailValidator
        
        Raises:
            ValidationError: If validation fails
        """
        from django.core.exceptions import ValidationError
        from django.core.validators import EmailValidator, RegexValidator
        
        # Validate city name (no numbers allowed)
        if self.city:
            city_validator = RegexValidator(
                regex=r'^[^0-9]+$',
                message='City field cannot contain numbers.',
                code='invalid_city'
            )
            try:
                city_validator(self.city)
            except ValidationError as e:
                raise ValidationError({'city': e.message})
        
        # Validate email format
        if self.email:
            email_validator = EmailValidator(message='Enter a valid email address.')
            try:
                email_validator(self.email)
            except ValidationError as e:
                raise ValidationError({'email': e.message})

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def email_user(self, subject, message, from_email=None, **kwargs) -> bool:
        """
        Send an email to this user with improved error handling.
        
        Args:
            subject: Email subject line
            message: Email message content
            from_email: Sender email address (defaults to DEFAULT_FROM_EMAIL)
            **kwargs: Additional arguments to pass to send_mail
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        from django.core.mail import send_mail, BadHeaderError
        try:
            send_mail(subject, message, from_email, [self.email], **kwargs)
            return True
        except BadHeaderError:
            logger.error(f"BadHeaderError when sending email to {self.email}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {self.email}: {str(e)}")
            return False

class MemberProfile(models.Model):
    """
    Profile model for members in the Raildrops system.
    
    Extends the base User model with additional member-specific fields.
    Links directly to a User model via OneToOneField with CASCADE deletion.
    Used for storing member preferences and profile data beyond authentication.
    
    Attributes:
        user: Link to the User model this profile belongs to
        city: The member's city/location for giveaway participation
        profile_image: Optional profile picture for the member
        created_at: Timestamp when this profile was created
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="member_profile",
        help_text="The user this member profile belongs to"
    )
    city = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        db_index=True,  # Add index for location-based queries
        help_text="Member's city for location-based giveaways"
    )
    profile_image = models.ImageField(
        upload_to="profile_images/", 
        blank=True, 
        null=True,
        help_text="Member's profile picture"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,  # Add index for timestamp-based queries
        help_text="When this profile was created"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'city']),  # Composite index for user+city queries
        ]

    def __str__(self) -> str:
        """Return a string representation of this member profile."""
        return f"{self.user.email} - {self.city or ''}"
        
    def clean(self) -> None:
        """Validate the model fields before saving.
        
        Performs custom validation on city field:
        - Ensures city name doesn't contain numbers
        
        Raises:
            ValidationError: If validation fails
        """
        from django.core.exceptions import ValidationError
        from django.core.validators import RegexValidator
        
        # Validate city name (no numbers allowed)
        if self.city:
            city_validator = RegexValidator(
                regex=r'^[^0-9]+$',
                message='City field cannot contain numbers.',
                code='invalid_city'
            )
            try:
                city_validator(self.city)
            except ValidationError as e:
                raise ValidationError({'city': e.message})
                
    def save(self, *args, **kwargs) -> None:
        """
        Override save method to ensure validation is performed before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)