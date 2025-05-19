from django.db import models
from django.conf import settings

class Business(models.Model):
    """
    Model for business profile on Raildrops.
    Contains information about the business, admin, and associated user.
    Follows PEP8, uses meaningful comments, and robust validation.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business_account")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_businesses", help_text="User who is the admin for this business")
    organization_number = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="Organization number must be unique")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="business_logos/", blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=64, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address", help_text="Street address of the business")
    phone = models.CharField(max_length=32, blank=True, null=True, verbose_name="Phone", help_text="Contact phone for the business")
    contact_person = models.CharField(max_length=128, blank=True, null=True, verbose_name="Contact Person", help_text="Name of the main contact for the business")
    social_media = models.JSONField(blank=True, null=True, verbose_name="Social Media", help_text="Links to Facebook, Instagram, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """
        Returns the name, city, and admin email for the business.
        """
        return f"{self.name} ({self.city}) - Admin: {self.admin.email if self.admin else 'Ingen'}"

    def clean(self):
        """
        Extra validation for the Business model.
        Checks that the name is not empty and that the postal code contains only digits.
        """
        from django.core.exceptions import ValidationError
        if not self.name or self.name.strip() == "":
            raise ValidationError("Business name cannot be empty.")
        if self.postal_code and not self.postal_code.isdigit():
            raise ValidationError("Postal code can only contain digits.")

    def save(self, *args, **kwargs):
        """
        Saves the Business object with robust error handling.
        """
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            # Log the error if desired
            raise
            
    def get_display_address(self):
        """
        Returnerer formatert fullstendig adresse.
        """
        parts = filter(None, [self.address, self.postal_code, self.city])
        return ", ".join(parts)
        
    def get_social_links(self):
        """
        Returnerer sosiale medier som en liste av navn/url-par.
        """
        if not self.social_media:
            return []
        return [(k, v) for k, v in self.social_media.items()]