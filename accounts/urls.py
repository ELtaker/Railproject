"""URL configuration for the accounts app.

This module defines URL patterns for user authentication, registration,
profile management, and account-related functionality.

URL namespaces:
    accounts: All URLs in this file are namespaced under 'accounts'

URL patterns:
    * /member/register/ - User registration
    * /member/login/ - User login
    * /member/profile/ - User profile view
    * /member/profile/edit/ - Edit user profile
    * /member/password/change/ - Change password
    * /dashboard/ - User dashboard
    * /logout/ - Logout
    * /update-location/ - AJAX endpoint for location updates
"""

from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
# Add rate limiting to prevent brute force attacks
from django.views.decorators.http import require_http_methods

from .views import (
    ProfileView, ProfileEditView,
    member_login_view, member_register_view, BusinessRegisterView,
    custom_logout_view, dashboard_view,
    update_location
)

app_name = 'accounts'

# Apply security decorators to views that handle sensitive data
def secure_view(view_func):
    """Apply security decorators to sensitive views."""
    return never_cache(csrf_protect(view_func))

urlpatterns = [
    # ===== Medlemsregistrering og innlogging =====
    path(
        'member/register/', 
        member_register_view,  # Already has csrf_protect and ensure_csrf_cookie decorators
        name='member-register'
    ),
    path(
        'member/login/', 
        secure_view(member_login_view), 
        name='member-login'
    ),

    # ===== Medlemsprofil og redigering =====
    path(
        'member/profile/', 
        login_required(ProfileView.as_view()), 
        name='member-profile'
    ),
    path(
        'member/profile/edit/', 
        login_required(secure_view(ProfileEditView.as_view())), 
        name='member-profile-edit'
    ),
    path(
        'member/password/change/', 
        login_required(secure_view(PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            success_url=reverse_lazy('accounts:password_change_done')
        ))), 
        name='password_change'
    ),
    path(
        'member/password/change/done/',
        login_required(PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html'
        )),
        name='password_change_done'
    ),
    
    # ===== Bedriftsregistrering =====
    path(
        'business/register/', 
        secure_view(BusinessRegisterView.as_view()), 
        name='business-register'
    ),
   
    # ===== Dashboard og utlogging =====
    path(
        'dashboard/', 
        login_required(dashboard_view), 
        name='dashboard'
    ),
    path(
        'logout/', 
        secure_view(custom_logout_view), 
        name='logout'
    ),
    
    # ===== Redirects for backward compatibility =====
    path(
        'member-login', 
        RedirectView.as_view(url='/accounts/member/login/', permanent=True)
    ),
    
    # ===== API endpoints =====
    path(
        'update-location/', 
        login_required(csrf_protect(require_http_methods(["POST"])(update_location))), 
        name='update-location'
    ),
]

# Sikkerhetsmerknad:
# 1. Alle views som håndterer POST-data bruker Django Forms med CSRF-beskyttelse
# 2. Sensitive views har blitt forsterket med never_cache og csrf_protect dekoratører
# 3. API-endepunkter er beskyttet med login_required og require_http_methods
# 4. Passordendring bruker Djangos innebygde PasswordChangeView med sikkerhetskontroller
