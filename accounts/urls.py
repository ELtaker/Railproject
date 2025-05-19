app_name = 'accounts'
from django.urls import path
from django.views.generic.base import RedirectView
from .views import (
    UserRegisterView, ProfileView, ProfileEditView,
    member_login_view, BusinessRegisterView,
    custom_logout_view, dashboard_view,
    BusinessLoginView, BusinessDashboardView
)
from businesses.views import BusinessProfileView, BusinessProfileEditView


urlpatterns = [
    
    # Medlemsregistrering og innlogging
    path('member/register/', UserRegisterView.as_view(), name='member-register'),
    path('member/login/', member_login_view, name='member-login'),

    # Medlemsprofil og redigering
    path('member/profile/', ProfileView.as_view(), name='member-profile'),
    path('member/profile/edit/', ProfileEditView.as_view(), name='member-profile-edit'),
    # Bedriftsregistrering
    path('business/register/', BusinessRegisterView.as_view(), name='business-register'),
   
    # Dashboard og logout
    path('dashboard/', dashboard_view, name='dashboard'),
    path('business/dashboard/', BusinessDashboardView.as_view(), name='business-dashboard'),
    path('logout/', custom_logout_view, name='logout'),
    # Bedriftsprofil og redigering
    path('business/profile/', BusinessProfileView.as_view(), name='business-profile'),
    path('business/profile/edit/', BusinessProfileEditView.as_view(), name='business-profile-edit'),
    
    # Redirects
    path('member-login', RedirectView.as_view(url='/accounts/member/login/', permanent=True)),
]

# Alle views som håndterer POST-data bruker Django Forms og har CSRF-beskyttelse by default.
