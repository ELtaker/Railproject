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
    """
    ModelForm for registrering av nye medlemmer på Raildrops.
    Inkluderer e-post, brukernavn, fornavn, etternavn og passord.
    Følger beste praksis for validering og robusthet.
    """
    """
    ModelForm for registrering av nye medlemmer på Raildrops.
    Inkluderer e-post, brukernavn, fornavn, etternavn og passord.
    """
    password1 = forms.CharField(
        label=_('Passord'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=_('Minst 8 tegn. Bør ikke være for lett å gjette.'),
    )
    password2 = forms.CharField(
        label=_('Bekreft passord'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=_('Skriv inn samme passord som ovenfor.'),
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        field_classes = {"username": UsernameField}

    def clean_password2(self) -> str:
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            logger.warning("Passordene matcher ikke under registrering.")
            raise forms.ValidationError("Passordene matcher ikke.")
        return password2

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        logger.info(f"Ny bruker registrert: {user.username} ({user.email})")
        return user

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    """
    Skjema for redigering av medlemsprofil. Tillater endring av e-post, navn, profilbilde og by.
    """
    city = forms.CharField(label="By", max_length=100, required=False, help_text="Skriv inn din bostedsby eller tettsted.")
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "profile_image", "city")
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            logger.warning(f"E-post {email} er allerede i bruk av en annen bruker.")
            raise forms.ValidationError("Denne e-posten er allerede i bruk.")
        return email

    """
    ModelForm for registrering av nye medlemmer på Raildrops.
    Inkluderer e-post, brukernavn, fornavn, etternavn og passord.
    """
    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=_('Minst 8 tegn. Bør ikke være for lett å gjette.'),
    )
    password2 = forms.CharField(
        label=_('Bekreft passord'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=_('Skriv inn samme passord som ovenfor for verifisering.'),
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        field_classes = {"username": UsernameField}
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_password2(self):
        """
        Validerer at passord og bekreft-passord matcher.
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            logger.warning("Passordene samsvarer ikke ved registrering.")
            raise forms.ValidationError(_("Passordene samsvarer ikke."))
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        logger.info(f"Ny bruker registrert: {user.username} ({user.email})")
        return user
