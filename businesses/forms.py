import json
import logging
import bleach
from typing import Any, Dict, Optional

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Business

logger = logging.getLogger(__name__)

class BusinessForm(forms.ModelForm):
    """
    Form for editing business profiles using the Business model.
    Implements best practices for validation, Bootstrap 5, and accessibility.
    
    This form provides comprehensive validation for all business profile fields,
    sanitizes inputs for security, and includes accessibility features following
    WCAG guidelines.
    """
    # Add explicit fields for better control and validation
    social_media_facebook = forms.URLField(
        required=False, 
        label=_('Facebook'),
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://facebook.com/yourbusiness',
            'aria-label': _('Facebook-side'),
        })
    )
    
    social_media_instagram = forms.URLField(
        required=False, 
        label=_('Instagram'),
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://instagram.com/yourbusiness',
            'aria-label': _('Instagram-profil'),
        })
    )
    
    social_media_linkedin = forms.URLField(
        required=False, 
        label=_('LinkedIn'),
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://linkedin.com/company/yourbusiness',
            'aria-label': _('LinkedIn-side'),
        })
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set up social media fields from JSON.
        """
        super().__init__(*args, **kwargs)
        
        # Set up help texts for better user guidance
        self.fields['name'].help_text = _('Offisielt bedriftsnavn som vist til brukere')
        self.fields['description'].help_text = _('Kort beskrivelse av bedriften (maks 500 tegn)')
        self.fields['phone'].help_text = _('Format: +XX XXX XX XXX')
        self.fields['postal_code'].help_text = _('4 eller 5 sifre')
        
        # Populate social media fields from the model's JSON field
        instance = kwargs.get('instance')
        if instance and instance.social_media:
            try:
                social_data = instance.social_media
                if 'facebook' in social_data:
                    self.fields['social_media_facebook'].initial = social_data['facebook']
                if 'instagram' in social_data:
                    self.fields['social_media_instagram'].initial = social_data['instagram']
                if 'linkedin' in social_data:
                    self.fields['social_media_linkedin'].initial = social_data['linkedin']
            except (TypeError, ValueError) as e:
                logger.warning(f"Error parsing social media data: {e}")
    
    def clean_postal_code(self) -> str:
        """
        Validate that postal code contains only digits and has correct length.
        """
        code = self.cleaned_data.get('postal_code', '')
        if code:
            code = code.strip()
            if not code.isdigit():
                raise forms.ValidationError(_('Postnummer må være kun sifre.'))
            if len(code) not in [4, 5]:
                raise forms.ValidationError(_('Postnummer må være 4 eller 5 sifre.'))
        return code

    def clean_website(self) -> Optional[str]:
        """
        Ensure website URLs start with http:// or https:// and sanitize.
        """
        website = self.cleaned_data.get('website')
        if website:
            website = website.strip()
            if not website.startswith(('http://', 'https://')):
                website = f"https://{website}"
            # Sanitize URL to prevent XSS
            website = bleach.clean(website)
        return website

    def clean_name(self) -> str:
        """
        Ensure business name is unique and sanitized.
        """
        name = self.cleaned_data.get("name", "")
        if name:
            name = bleach.clean(name.strip())
            if not name:
                raise forms.ValidationError(_('Bedriftsnavn kan ikke være tomt.'))
                
            # Check uniqueness but exclude current instance
            if Business.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
                logger.warning(f"Bedriftsnavn '{name}' er allerede i bruk.")
                raise forms.ValidationError(_('Dette bedriftsnavnet er allerede registrert.'))
        return name

    def clean_phone(self) -> Optional[str]:
        """
        Validate phone number format and sanitize.
        """
        phone = self.cleaned_data.get('phone', '')
        if phone:
            phone = phone.strip()
            # Allow digits, +, and spaces in phone numbers
            if not all(c in '0123456789+ ' for c in phone):
                raise forms.ValidationError(_('Telefonnummer kan kun inneholde sifre, + og mellomrom.'))
            # Sanitize phone to prevent XSS
            phone = bleach.clean(phone)
        return phone
        
    def clean_description(self) -> str:
        """
        Sanitize description to prevent XSS attacks.
        """
        description = self.cleaned_data.get('description', '')
        if description:
            # Allow only safe HTML tags in description
            allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
            description = bleach.clean(description, tags=allowed_tags, strip=True)
        return description
        
    def clean_contact_person(self) -> Optional[str]:
        """
        Sanitize contact person name to prevent XSS attacks.
        """
        contact = self.cleaned_data.get('contact_person', '')
        if contact:
            contact = bleach.clean(contact.strip())
        return contact

    def clean(self) -> Dict[str, Any]:
        """
        Process the form data and handle social media fields.
        """
        cleaned_data = super().clean()
        
        # Process social media fields into a JSON structure
        social_media = {}
        
        facebook = cleaned_data.get('social_media_facebook')
        instagram = cleaned_data.get('social_media_instagram')
        linkedin = cleaned_data.get('social_media_linkedin')
        
        if facebook:
            social_media['facebook'] = bleach.clean(facebook)
        if instagram:
            social_media['instagram'] = bleach.clean(instagram)
        if linkedin:
            social_media['linkedin'] = bleach.clean(linkedin)
            
        # Only update if we have social media data
        if social_media:
            cleaned_data['social_media'] = social_media
            
        return cleaned_data
    
    class Meta:
        model = Business
        fields = [
            'name', 'description', 'logo', 'website', 'postal_code', 'city',
            'address', 'phone', 'contact_person'
        ]
        # Note: social_media is handled via custom fields, so it's not in the fields list
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Bedriftsnavn',
                'aria-label': 'Bedriftsnavn',
                'autocomplete': 'organization',
                'maxlength': '255',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Skriv en kort beskrivelse av bedriften din', 
                'rows': 4,
                'aria-label': 'Beskrivelse',
                'maxlength': '500'
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-file',
                'aria-label': 'Bedriftslogo',
                'accept': 'image/*'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://www.dinbedrift.no',
                'aria-label': 'Nettside',
                'pattern': 'https?://.+',
                'autocomplete': 'url'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '0123',
                'aria-label': 'Postnummer',
                'pattern': '[0-9]{4,5}',
                'title': 'Postnummer må være 4 eller 5 sifre',
                'autocomplete': 'postal-code',
                'inputmode': 'numeric'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Oslo',
                'aria-label': 'Sted',
                'autocomplete': 'address-level2'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Storgata 1',
                'aria-label': 'Gateadresse',
                'autocomplete': 'street-address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+47 123 45 678',
                'aria-label': 'Telefonnummer',
                'pattern': '[0-9+\s]{8,15}',
                'title': 'Telefonnummer må inneholde 8-15 sifre, kan inkludere + og mellomrom',
                'autocomplete': 'tel',
                'inputmode': 'tel'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ola Nordmann',
                'aria-label': 'Kontaktperson',
                'autocomplete': 'name'
            }),
        }
        
        labels = {
            'name': _('Bedriftsnavn'),
            'description': _('Beskrivelse'),
            'logo': _('Bedriftslogo'),
            'website': _('Nettside'),
            'postal_code': _('Postnummer'),
            'city': _('Sted'),
            'address': _('Gateadresse'),
            'phone': _('Telefonnummer'),
            'contact_person': _('Kontaktperson'),
        }
        
        error_messages = {
            'name': {
                'required': _('Bedriftsnavn er påkrevd'),
                'max_length': _('Bedriftsnavn kan ikke være lengre enn 255 tegn')
            },
            'postal_code': {
                'max_length': _('Postnummer kan ikke være lengre enn 10 tegn')
            },
            'city': {
                'max_length': _('Stedsnavn kan ikke være lengre enn 64 tegn')
            }
        }
