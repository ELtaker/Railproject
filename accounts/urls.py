app_name = 'accounts'
from django.urls import path
from django.views.generic.base import RedirectView
from .views import (
    UserRegisterView, ProfileView, ProfileEditView,
    member_login_view, company_login_view, CompanyRegisterView,
    custom_logout_view, dashboard_view, BusinessProfileEditView
)

urlpatterns = [
    # Medlemsregistrering og innlogging
    path('member/register/', UserRegisterView.as_view(), name='member_register'),
    path('member/login/', member_login_view, name='member_login'),
    # Bedriftsregistrering og innlogging
    path('company/register/', CompanyRegisterView.as_view(), name='company_register'),
    path('company/login/', company_login_view, name='company_login'),
    # Dashboard og logout
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', custom_logout_view, name='logout'),
    # Medlemsprofil og redigering
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('business-profile/edit/', BusinessProfileEditView.as_view(), name='business_profile_edit'),
    path('member-login', RedirectView.as_view(url='/accounts/member/login/', permanent=True)),
]

