from django.contrib.auth.models import AbstractUser, AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):
    """
    Utvidet bruker for Raildrops. Kun generelle brukerfelt.
    """
    profile_image = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Profilbilde for brukeren."
    )
    city = models.CharField(max_length=100, blank=True, help_text="Brukerens bostedsby/sted.")

    def __str__(self) -> str:
        return self.email or self.username

class CompanyManager(BaseUserManager):
    """
    Manager for Company-modellen.
    """
    def create_user(
        self, email: str, company_name: str, organization_number: str, password: str = None, **extra_fields
    ) -> 'Company':
        """
        Opprett og returner en ny bedriftsbruker.
        """
        if not email:
            logger.error('Bedriftsbruker mangler e-postadresse')
            raise ValueError('Bedriftsbruker må ha e-postadresse')
        if not company_name:
            logger.error('Bedriftsbruker mangler selskapsnavn')
            raise ValueError('Bedriftsbruker må ha navn på selskap')
        if not organization_number:
            logger.error('Bedriftsbruker mangler organisasjonsnummer')
            raise ValueError('Bedriftsbruker må ha organisasjonsnummer')
        email = self.normalize_email(email)
        company = self.model(
            email=email,
            company_name=company_name,
            organization_number=organization_number,
            **extra_fields
        )
        company.set_password(password)
        company.save(using=self._db)
        logger.info(f"Bedriftsbruker opprettet: {company}")
        return company

    def create_superuser(
        self, email: str, company_name: str, organization_number: str, password: str = None, **extra_fields
    ) -> 'Company':
        """
        Opprett og returner en ny superuser-bedrift.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser må ha is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser må ha is_superuser=True.')
        return self.create_user(email, company_name, organization_number, password, **extra_fields)

class Company(AbstractBaseUser, PermissionsMixin):
    """
    Modell for bedriftsbruker.
    """
    company_name = models.CharField(max_length=255, help_text="Navn på selskapet.")
    organization_number = models.CharField(max_length=20, unique=True, help_text="Organisasjonsnummer.")
    email = models.EmailField(unique=True, help_text="Bedriftens e-postadresse.")
    first_name = models.CharField(max_length=100, help_text="Fornavn på kontaktperson.", blank=True, null=True, default="")
    last_name = models.CharField(max_length=100, help_text="Etternavn på kontaktperson.", blank=True, null=True, default="")
    address = models.CharField(max_length=255, help_text="Adresse til bedriften.", blank=True, null=True, default="")
    postal_code = models.CharField(max_length=10, help_text="Postnummer.", blank=True, null=True, default="")
    city = models.CharField(max_length=100, help_text="Poststed/by.", blank=True, null=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='company_set',
        blank=True,
        help_text='The groups this company belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='company_user_permissions',
        blank=True,
        help_text='Specific permissions for this company.',
        verbose_name='user permissions',
    )

    objects = CompanyManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['company_name', 'organization_number', 'first_name', 'last_name', 'address', 'postal_code', 'city']

    def __str__(self) -> str:
        """
        Returnerer selskapsnavn og e-post.
        """
        return f"{self.company_name} ({self.email})"