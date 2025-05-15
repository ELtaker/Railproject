import logging
from django import forms
from .models import Business

logger = logging.getLogger(__name__)

class BusinessForm(forms.ModelForm):
    """
    Skjema for redigering av bedriftsprofil. Bruker Business-modellen.
    Følger beste praksis for validering, Bootstrap 5 og robusthet.
    """
    def clean_postal_code(self):
        code = self.cleaned_data.get('postal_code')
        if code and (not code.isdigit() or len(code) not in [4, 5]):
            raise forms.ValidationError("Postnummer må være 4 eller 5 sifre.")
        return code

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            raise forms.ValidationError("Nettside må starte med http:// eller https://")
        return website

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if Business.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
            logger.warning(f"Bedriftsnavn {name} er allerede i bruk.")
            raise forms.ValidationError("Dette bedriftsnavnet er allerede registrert.")
        return name

    class Meta:
        model = Business
        fields = ['name', 'description', 'logo', 'website', 'postal_code', 'city']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bedriftsnavn'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Beskrivelse', 'rows': 4}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postnummer'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sted'}),
        }
