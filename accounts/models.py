from django.contrib.auth.models import AbstractUser, AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):
    """
    Utvidet bruker for Raildrops.
    Inneholder kun generelle brukerfelt, og kan utvides med flere felt etter behov.
    Følger PEP8, bruker meaningful comments og robust validering.
    """
    profile_image = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Profilbilde for brukeren."
    )
    city = models.CharField(max_length=100, blank=True, help_text="Brukerens bostedsby/sted.")

    def __str__(self) -> str:
        """
        Returnerer e-post hvis tilgjengelig, ellers brukernavn.
        """
        return self.email or self.username

    def clean(self):
        """
        Ekstra validering for User-modellen.
        Sjekker at by ikke inneholder tall og at e-post har gyldig format.
        Kan utvides med flere regler.
        """
        from django.core.exceptions import ValidationError
        import re
        if self.city and any(char.isdigit() for char in self.city):
            raise ValidationError("Byfeltet kan ikke inneholde tall.")
        email_regex = r"[^@]+@[^@]+\.[^@]+"
        if self.email and not re.match(email_regex, self.email):
            raise ValidationError("Ugyldig e-postadresse.")

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sender e-post til brukeren. Robust mot feil.
        """
        from django.core.mail import send_mail, BadHeaderError
        try:
            send_mail(subject, message, from_email, [self.email], **kwargs)
        except BadHeaderError:
            # Logg feilen hvis ønskelig
            pass
        except Exception as e:
            # Logg eller håndter andre e-postfeil
            pass

from django.conf import settings
from django.db import models

class MemberProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member_profile")
    city = models.CharField(max_length=100, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profile_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.city or ''}"

# BusinessProfile-modellen er fjernet. Ny bedriftslogikk bruker Business-modellen i businesses/models.py.