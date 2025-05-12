from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from .models import Company

class EmailBackend(ModelBackend):
    """
    Autentiserer brukere (User) med e-post og passord.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get('email')
        if email is None or password is None:
            return None
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except UserModel.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None


class CompanyAuthBackend(ModelBackend):
    """
    Egendefinert autentiseringsbackend for Company-modellen (bedriftsbrukere).
    Autentiserer med e-post og passord.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get('email')
        if email is None or password is None:
            return None
        try:
            company = Company.objects.get(email=email)
            if company.check_password(password) and self.user_can_authenticate(company):
                return company
        except Company.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return Company.objects.get(pk=user_id)
        except Company.DoesNotExist:
            return None
