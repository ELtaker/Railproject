from businesses.models import Business

import logging
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)


from django.contrib.auth import authenticate

class MemberLoginForm(forms.Form):
    """Login-form for medlemmer."""
    email = forms.EmailField(label=_('E-post'))
    password = forms.CharField(label=_('Passord'), widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            user = authenticate(
                request=self.request,
                email=email,
                password=password,
                backend='accounts.backends.EmailBackend'
            )
            if user is None:
                logger.warning(f"Mislykket innlogging for e-post: {email}")
                raise forms.ValidationError(_('Ugyldig e-post eller passord.'))
            cleaned_data['user'] = user
        return cleaned_data

class BusinessRegistrationForm(forms.ModelForm):
    company_name = forms.CharField(label='Bedriftsnavn', max_length=255)
    organization_number = forms.CharField(label='Organisasjonsnummer', max_length=20)
    address = forms.CharField(label='Adresse', max_length=255)
    postal_code = forms.CharField(label='Postnummer', max_length=10)
    city = forms.CharField(label='Poststed/by', max_length=100)
    password1 = forms.CharField(label='Passord', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Bekreft passord', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'company_name', 'organization_number', 'address', 'postal_code', 'city', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'organization'}),
            'organization_number': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'address-line1'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'postal-code'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'address-level2'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        }

    def clean_email(self):
        """
        Validerer at e-postadressen ikke allerede er i bruk.
        Fanger opp duplikater før lagring.
        """
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Denne e-posten er allerede i bruk.')
        return email

    def clean_organization_number(self):
        """
        Validerer at organisasjonsnummeret er unikt for Business.
        """
        orgnr = self.cleaned_data['organization_number']
        if Business.objects.filter(organization_number=orgnr).exists():
            raise forms.ValidationError('Dette organisasjonsnummeret er allerede i bruk.')
        return orgnr

    def clean(self):
        """
        Tverrfelt-validering for passord.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passordene matcher ikke.')
        return cleaned_data

    def save(self, commit=True):
        """
        Oppretter bruker og tilknyttet Business atomisk.
        Brukeren blir admin for bedriften.
        Følger robust feilkontroll og god praksis.
        """
        from businesses.models import Business
        from django.db import transaction
        try:
            with transaction.atomic():
                user = super().save(commit=False)
                user.set_password(self.cleaned_data['password1'])
                # Sett username til e-post hvis ikke satt
                if not user.username:
                    user.username = self.cleaned_data['email']
                if commit:
                    user.save()
                    business = Business(
                        user=user,
                        admin=user,  # Brukeren som admin
                        name=self.cleaned_data['company_name'],
                        description='',
                        website=None,
                        postal_code=self.cleaned_data['postal_code'],
                        city=self.cleaned_data['city'],
                    )
                    business.save()
                return user
        except Exception as e:
            logger.error(f"Feil ved opprettelse av bedriftsbruker og Business: {e}")
            raise forms.ValidationError('Det oppstod en feil under registrering. Prøv igjen.')


from django.contrib.auth import authenticate

# BusinessProfileForm er fjernet. Bruk Business-modellen fra businesses/forms.py for bedriftsprofil-redigering.
class UserRegistrationForm(forms.ModelForm):
    """ModelForm for registration of new members on Raildrops.
    Includes email, username, first name, last name, city and password.
    
    Implements security best practices like password validation,
    XSS protection, and proper error messages in Norwegian.
    """
    password1 = forms.CharField(
        label=_('Passord'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'aria-describedby': 'passwordHelp'
        }),
        help_text=_('Minst 8 tegn. Bør ikke være for lett å gjette.'),
    )
    password2 = forms.CharField(
        label=_('Bekreft passord'),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control'
        }),
        strip=False,
        help_text=_('Skriv inn samme passord som ovenfor.'),
    )
    city = forms.CharField(
        label=_('By'),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'autocomplete': 'address-level2',
            'class': 'form-control',
            'placeholder': 'F.eks. Oslo, Bergen, Trondheim'
        }),
        help_text=_('Din lokasjon for å delta i lokale giveaways.')    
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "city")
        field_classes = {"username": UsernameField}
        widgets = {
            "username": forms.TextInput(attrs={
                "autocomplete": "username",
                "class": "form-control",
                "placeholder": "Velg et brukernavn",
                "aria-describedby": "usernameHelp"
            }),
            "email": forms.EmailInput(attrs={
                "autocomplete": "email",
                "class": "form-control",
                "placeholder": "din.epost@eksempel.no",
                "aria-describedby": "emailHelp"
            }),
            "first_name": forms.TextInput(attrs={
                "autocomplete": "given-name",
                "class": "form-control",
                "placeholder": "Fornavn"
            }),
            "last_name": forms.TextInput(attrs={
                "autocomplete": "family-name",
                "class": "form-control",
                "placeholder": "Etternavn"
            }),
        }
        help_texts = {
            "username": _('Påkrevd. 150 tegn eller mindre. Bokstaver, tall og @/./+/-/_.'),
            "email": _('Din e-postadresse. Brukes for innlogging.'),
        }
    
    # XSS Prevention
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '')
        from django.utils.html import strip_tags
        return strip_tags(first_name)
        
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '')
        from django.utils.html import strip_tags
        return strip_tags(last_name)
        
    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        from django.utils.html import strip_tags
        return strip_tags(username)
        
    def clean_city(self):
        city = self.cleaned_data.get('city', '')
        from django.utils.html import strip_tags
        city = strip_tags(city)
        
        # Validate city format (no numbers allowed)
        import re
        if city and re.search(r'[0-9]', city):
            raise forms.ValidationError(_('Bynavn kan ikke inneholde tall.'))
        
        return city
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('Denne e-postadressen er allerede i bruk.'))
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('De to passordene er ikke like.'))
            
        # Check for minimum password strength
        if len(password1) < 8:
            raise forms.ValidationError(_('Passordet må være minst 8 tegn langt.'))
            
        # Check for common passwords
        common_passwords = ['password', 'password123', '12345678', 'qwerty', 'abc123']
        if password1.lower() in common_passwords:
            raise forms.ValidationError(_('Dette passordet er for vanlig og usikkert.'))
            
        return password2

    def save(self, commit: bool = True):
        """Save the user model with the cleaned data and create Member Group association.
        
        Args:
            commit: Whether to save the model instance
        Returns:
            User: The created user instance
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data["email"].lower()  # Ensure email is lowercase
        if commit:
            user.save()
            # Create MemberProfile for the user
            try:
                from .models import MemberProfile
                MemberProfile.objects.create(
                    user=user,
                    city=self.cleaned_data.get('city', '')
                )
                logger.info(f"Created MemberProfile for new user: {user.username}")
            except Exception as e:
                logger.error(f"Failed to create MemberProfile for {user.username}: {str(e)}")
        return user

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    """Form for editing member profile. Allows changing email, name, profile image and city."""
    city = forms.CharField(
        label=_('By'),
        max_length=100, 
        required=False, 
        help_text=_('Skriv inn byen din for å delta i lokale giveaways.'),
        widget=forms.TextInput(attrs={
            'autocomplete': 'address-level2',
            'class': 'form-control',
            'placeholder': 'F.eks. Oslo, Bergen, Trondheim'
        })
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "profile_image", "city")
        widgets = {
            "email": forms.EmailInput(attrs={
                "autocomplete": "email",
                "class": "form-control",
                "aria-describedby": "emailHelp"
            }),
            "first_name": forms.TextInput(attrs={
                "autocomplete": "given-name",
                "class": "form-control",
                "placeholder": "Fornavn"
            }),
            "last_name": forms.TextInput(attrs={
                "autocomplete": "family-name",
                "class": "form-control",
                "placeholder": "Etternavn"
            }),
            "profile_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*"
            }),
        }
        
    # Add sanitization for XSS prevention
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '')
        # Remove potentially dangerous HTML tags
        from django.utils.html import strip_tags
        return strip_tags(first_name)
        
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '')
        from django.utils.html import strip_tags
        return strip_tags(last_name)
        
    def clean_city(self):
        city = self.cleaned_data.get('city', '')
        from django.utils.html import strip_tags
        city = strip_tags(city)
        
        # Validate city format (no numbers allowed)
        import re
        if city and re.search(r'[0-9]', city):
            raise forms.ValidationError(_('Bynavn kan ikke inneholde tall.'))
        
        return city
        
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if email != self.instance.email.lower():
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError("Denne e-postadressen er allerede i bruk.")
        return email

    def save(self, commit=True):
        """
        Save method to properly handle city data for the user profile.
        
        Args:
            commit: Whether to save the model instance
        Returns:
            User: The updated user instance
        """
        user = super().save(commit=False)
        
        # Ensure we update the city field correctly
        city = self.cleaned_data.get('city', '')
        user.city = city
        
        if commit:
            user.save()
            
            # Update the MemberProfile if it exists
            try:
                if hasattr(user, 'member_profile'):
                    profile = user.member_profile
                    profile.city = city
                    profile.save()
            except Exception as e:
                logger.error(f"Failed to update member profile for {user.email}: {str(e)}")
                
        return user
