from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class User(AbstractUser):
    """
    Custom user model for Raildrops.
    Uses email as the primary login identifier and enforces unique, lowercase emails.
    Includes profile image and city fields.
    """
    email = models.EmailField(_('email address'), unique=True, help_text="Unique email address for login.")
    profile_image = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Profile image for the user."
    )
    city = models.CharField(max_length=100, blank=True, help_text="User's city/location.")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username is still required for admin compatibility

    def __str__(self) -> str:
        return self.email or self.username

    def clean(self):
        from django.core.exceptions import ValidationError
        import re
        if self.city and any(char.isdigit() for char in self.city):
            raise ValidationError("City field cannot contain numbers.")
        email_regex = r"[^@]+@[^@]+\.[^@]+"
        if self.email and not re.match(email_regex, self.email):
            raise ValidationError("Invalid email address.")

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def email_user(self, subject, message, from_email=None, **kwargs):
        from django.core.mail import send_mail, BadHeaderError
        try:
            send_mail(subject, message, from_email, [self.email], **kwargs)
        except BadHeaderError:
            pass  # Log error or handle appropriately
        except Exception as e:
            pass  # Log or handle other email errors

class MemberProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member_profile")
    city = models.CharField(max_length=100, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profile_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.city or ''}"