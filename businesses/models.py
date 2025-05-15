from django.db import models
from django.conf import settings

class Business(models.Model):
    """
    Modell for bedriftsprofil på Raildrops.
    Inneholder informasjon om bedrift, admin og tilknyttet bruker.
    Følger PEP8, bruker meaningful comments og robust validering.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business_account")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_businesses", help_text="Brukeren som er admin for denne bedriften")
    organization_number = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="Organisasjonsnummer må være unikt")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="business_logos/", blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """
        Returnerer navn, by og admin-e-post for bedriften.
        """
        return f"{self.name} ({self.city}) - Admin: {self.admin.email if self.admin else 'Ingen'}"

    def clean(self):
        """
        Ekstra validering for Business-modellen.
        Sjekker at navn ikke er tomt og at postnummer kun inneholder tall.
        """
        from django.core.exceptions import ValidationError
        if not self.name or self.name.strip() == "":
            raise ValidationError("Bedriftsnavn kan ikke være tomt.")
        if self.postal_code and not self.postal_code.isdigit():
            raise ValidationError("Postnummer kan kun inneholde tall.")

    def save(self, *args, **kwargs):
        """
        Lagrer Business-objektet med robust feilkontroll.
        """
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            # Logg feilen hvis ønskelig
            raise