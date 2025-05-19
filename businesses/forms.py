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

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.replace('+','').replace(' ','').isdigit():
            raise forms.ValidationError("Telefonnummer må kun inneholde sifre og evt. +.")
        return phone

    def clean_social_media(self):
        social = self.cleaned_data.get('social_media')
        if social and not isinstance(social, dict):
            raise forms.ValidationError("Sosiale medier må være et gyldig JSON-objekt, f.eks. {\"facebook\": \"url\", \"instagram\": \"url\"}.")
        return social

    class Meta:
        model = Business
        fields = [
            'name', 'description', 'logo', 'website', 'postal_code', 'city',
            'address', 'phone', 'contact_person', 'social_media'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Bedriftsnavn',
                'aria-label': 'Bedriftsnavn'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Beskrivelse', 
                'rows': 4,
                'aria-label': 'Beskrivelse'
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'aria-label': 'Bedriftslogo'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://',
                'aria-label': 'Nettside',
                'pattern': 'https?://.+'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Postnummer',
                'aria-label': 'Postnummer',
                'pattern': '[0-9]{4,5}',
                'title': 'Postnummer må være 4 eller 5 sifre'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Sted',
                'aria-label': 'Sted'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Gateadresse',
                'aria-label': 'Gateadresse'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Telefonnummer',
                'aria-label': 'Telefonnummer',
                'pattern': '[0-9+\s]{8,15}',
                'title': 'Telefonnummer må inneholde 8-15 sifre, kan inkludere + og mellomrom'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Kontaktperson',
                'aria-label': 'Kontaktperson'
            }),
            'social_media': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': '{"facebook": "url", "instagram": "url"}', 
                'rows': 2,
                'aria-label': 'Sosiale medier'
            }),
        }
