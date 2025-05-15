app_name = 'accounts'
from django.urls import path
from django.views.generic.base import RedirectView
from .views import (
    UserRegisterView, ProfileView, ProfileEditView,
    member_login_view, BusinessRegisterView,
    custom_logout_view, dashboard_view,
    BusinessLoginView, BusinessDashboardView
)

urlpatterns = [
    # Medlemsregistrering og innlogging
    path('member/register/', UserRegisterView.as_view(), name='member-register'),
    path('member/login/', member_login_view, name='member-login'),
    path('business/login/', BusinessLoginView.as_view(), name='business-login'),
    path('login/', member_login_view, name='login'),
    # Bedriftsregistrering
    path('business/register/', BusinessRegisterView.as_view(), name='business-register'),
    # Dashboard og logout
    path('dashboard/', dashboard_view, name='dashboard'),
    path('business/dashboard/', BusinessDashboardView.as_view(), name='business_dashboard'),
    path('logout/', custom_logout_view, name='logout'),
    # Medlemsprofil og redigering
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile-edit'),
    
    # Redirects
    path('member-login', RedirectView.as_view(url='/accounts/member/login/', permanent=True)),
]

# Alle views som håndterer POST-data bruker Django Forms og har CSRF-beskyttelse by default.
