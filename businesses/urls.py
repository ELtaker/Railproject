"""
URL configuration for the businesses app.

This module defines URL patterns for business registration, login, dashboard,
profile management, and public business profile views.

URL namespaces:
    businesses: All URLs in this file are namespaced under 'businesses'

URL patterns:
    * /register/ - Business registration
    * /login/ - Business login
    * /dashboard/ - Business dashboard
    * /profile/ - Business profile view
    * /profile/edit/ - Edit business profile
    * /<int:pk>/ - Public business profile view
"""

from django.urls import path
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

from .views import (
    BusinessRegisterView,
    BusinessLoginView,
    BusinessDashboardView,
    BusinessProfileView,
    BusinessProfileEditView,
    BusinessPublicProfileView,
)

app_name = 'businesses'

# Apply security decorators to views that handle sensitive data
def secure_view(view_func):
    """Apply security decorators to sensitive views."""
    return never_cache(csrf_protect(view_func))

urlpatterns = [
    # ===== Bedriftsregistrering og innlogging =====
    path(
        'register/', 
        secure_view(BusinessRegisterView.as_view()), 
        name='business-register'
    ),
    path(
        'login/', 
        secure_view(BusinessLoginView.as_view()), 
        name='business-login'
    ),
    
    # ===== Bedriftsdashboard og profil =====
    path(
        'dashboard/', 
        login_required(BusinessDashboardView.as_view()),
        name='business-dashboard'
    ),
    path(
        'profile/', 
        login_required(BusinessProfileView.as_view()), 
        name='business-profile'
    ),
    path(
        'profile/edit/', 
        login_required(secure_view(BusinessProfileEditView.as_view())), 
        name='business-profile-edit'
    ),
    
    # ===== Offentlig profil =====
    path(
        '<int:pk>/', 
        BusinessPublicProfileView.as_view(), 
        name='business-public-profile'
    ),
]