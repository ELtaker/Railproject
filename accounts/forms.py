import logging
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)

from .models import Company
from django.contrib.auth import authenticate

class MemberLoginForm(forms.Form):
    """Login-form for medlemmer."""
    email: forms.EmailField = forms.EmailField(label=_('E-post'))
    password: forms.CharField = forms.CharField(label=_('Passord'), widget=forms.PasswordInput)

    def clean(self) -> dict:
        """Validerer brukerens innloggingsdata."""
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            user = authenticate(request=self.request if hasattr(self, 'request') else None, email=email, password=password, backend='accounts.backends.EmailBackend')
            if user is None:
                logger.warning(f"Mislykket innlogging for e-post: {email}")
                raise forms.ValidationError(_('Ugyldig e-post eller passord.'))
            cleaned_data['user'] = user
        return cleaned_data

class CompanyRegistrationForm(forms.ModelForm):
    """Registreringsform for bedrifter."""
    first_name = forms.CharField(label=_('Fornavn'), max_length=100)
    last_name = forms.CharField(label=_('Etternavn'), max_length=100)
    address = forms.CharField(label=_('Adresse'), max_length=255)
    postal_code = forms.CharField(label=_('Postnummer'), max_length=10)
    city = forms.CharField(label=_('Poststed/by'), max_length=100)
    personvern = forms.BooleanField(label=_('Jeg har lest og aksepterer personvernerklæringen'), required=True)
    password1: forms.CharField = forms.CharField(label=_('Passord'), widget=forms.PasswordInput)
    password2: forms.CharField = forms.CharField(label=_('Bekreft passord'), widget=forms.PasswordInput)

    class Meta:
        model = Company
        fields = ['company_name', 'organization_number', 'email', 'first_name', 'last_name', 'address', 'postal_code', 'city', 'personvern']

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email')
        if Company.objects.filter(email=email).exists():
            logger.warning(f"Duplisert e-post ved bedriftsregistrering: {email}")
            raise forms.ValidationError(_('Denne e-posten er allerede i bruk for en bedrift.'))
        return email

    def clean_organization_number(self) -> str:
        orgnr = self.cleaned_data.get('organization_number')
        if Company.objects.filter(organization_number=orgnr).exists():
            logger.warning(f"Duplisert org.nr. ved bedriftsregistrering: {orgnr}")
            raise forms.ValidationError(_('Dette organisasjonsnummeret er allerede i bruk.'))
        return orgnr

    def clean_personvern(self):
        personvern = self.cleaned_data.get('personvern')
        if not personvern:
            raise forms.ValidationError(_('Du må akseptere personvernerklæringen for å registrere deg.'))
        return personvern

    def clean(self) -> dict:
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            logger.warning("Passordene matcher ikke ved bedriftsregistrering.")
            raise forms.ValidationError(_('Passordene matcher ikke.'))
        return cleaned_data

    def save(self, commit=True):
        company = super().save(commit=False)
        company.first_name = self.cleaned_data['first_name']
        company.last_name = self.cleaned_data['last_name']
        company.address = self.cleaned_data['address']
        company.postal_code = self.cleaned_data['postal_code']
        company.city = self.cleaned_data['city']
        company.set_password(self.cleaned_data['password1'])
        if commit:
            company.save()
            # Synkroniser Business-profil
            # company er allerede en AUTH_USER_MODEL-instans (User/Company)
            logger.info(f"[DEBUG] Type company: {type(company)} (should be AUTH_USER_MODEL)")
            business, created = Business.objects.get_or_create(
                user=company,
                defaults={
                    'name': company.company_name,
                    'city': company.city,
                    'postal_code': company.postal_code,
                    'admin': company  # Sett admin til company direkte
                }
            )
            if not created:
                business.name = company.company_name
                business.city = company.city
                business.postal_code = company.postal_code
                business.admin = company
                business.save()
        return company


class CompanyLoginForm(forms.Form):
    email = forms.EmailField(label=_('E-post'))
    password = forms.CharField(label=_('Passord'), widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        from .backends import CompanyAuthBackend
        backend = CompanyAuthBackend()
        import logging
        logger = logging.getLogger(__name__)
        if not email or not password:
            logger.warning(f"Ingen e-post eller passord oppgitt ved bedriftsinnlogging. Email: {email}")
            raise forms.ValidationError(_('Du må fylle ut både e-post og passord.'))
        try:
            from .models import Company
            company_obj = Company.objects.get(email=email)
        except Company.DoesNotExist:
            logger.warning(f"Bedriftsinnlogging: E-post ikke funnet: {email}")
            raise forms.ValidationError(_('Ugyldig e-post eller passord for bedrift.'))
        if not company_obj.check_password(password):
            logger.warning(f"Bedriftsinnlogging: Feil passord for e-post: {email}")
            raise forms.ValidationError(_('Ugyldig e-post eller passord for bedrift.'))
        if hasattr(company_obj, 'is_active') and not company_obj.is_active:
            logger.warning(f"Bedriftsinnlogging: Brukeren er inaktiv: {email}")
            raise forms.ValidationError(_('Denne bedriftskontoen er deaktivert. Kontakt support.'))
        logger.info(f"Bedrift innlogget: {email}")
        cleaned_data['company'] = company_obj
        return cleaned_data

from businesses.models import Business
from .models import Company
from django.contrib.auth import authenticate

class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'description', 'logo', 'website', 'postal_code', 'city']

class BusinessRegistrationForm(forms.ModelForm):
    """
    Skjema for registrering av bedriftsbruker og tilknyttet bedrift.
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
    business_name = forms.CharField(label=_('Bedriftsnavn'), max_length=255)
    description = forms.CharField(label=_('Beskrivelse'), widget=forms.Textarea, required=False)
    logo = forms.ImageField(label=_('Logo'), required=False)
    website = forms.URLField(label=_('Nettside'), required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        field_classes = {"username": UsernameField}

    def clean_password2(self) -> str:
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            logger.warning("Passordene matcher ikke under bedriftsregistrering.")
            raise forms.ValidationError("Passordene matcher ikke.")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            logger.warning(f"E-post {email} er allerede i bruk.")
            raise forms.ValidationError("Denne e-posten er allerede i bruk.")
        return email

    def clean_business_name(self):
        name = self.cleaned_data.get("business_name")
        if Business.objects.filter(name=name).exists():
            logger.warning(f"Bedriftsnavn {name} er allerede i bruk.")
            raise forms.ValidationError("Dette bedriftsnavnet er allerede registrert.")
        return name

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            business = Business(
                user=user,
                name=self.cleaned_data["business_name"],
                description=self.cleaned_data.get("description", ""),
                logo=self.cleaned_data.get("logo"),
                website=self.cleaned_data.get("website", "")
            )
            business.save()
            logger.info(f"Ny bedriftsbruker: {user.username} ({user.email}), bedrift: {business.name}")
        return user

class UserRegistrationForm(forms.ModelForm):
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
