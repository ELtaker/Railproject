import logging
from django import forms
from .models import Business

logger = logging.getLogger(__name__)

class BusinessProfileForm(forms.ModelForm):
    """
    Skjema for redigering av bedriftsprofil på Raildrops.
    Tillater endring av navn, beskrivelse, logo, nettside, postnummer og sted.
    """
    class Meta:
        model = Business
        fields = ("name", "description", "logo", "website", "postal_code", "city")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Beskrivelse av bedriften"}),
            "website": forms.URLInput(attrs={"placeholder": "https://"}),
            "postal_code": forms.TextInput(attrs={"placeholder": "Postnummer"}),
            "city": forms.TextInput(attrs={"placeholder": "Sted"}),
        }

    def clean_name(self) -> str:
        name = self.cleaned_data.get("name")
        if Business.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
            logger.warning(f"Bedriftsnavn {name} er allerede i bruk.")
            raise forms.ValidationError("Dette bedriftsnavnet er allerede registrert.")
        return name
