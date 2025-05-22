"""
URL configuration for the giveaways app.

This module defines URL patterns for giveaway listing, creation, and detail views.
Includes security decorators and proper organization.

URL namespaces:
    giveaways: All URLs in this file are namespaced under 'giveaways'

URL patterns:
    * / - Public giveaway listing page
    * /create/ - Create giveaway (business only)
    * /<int:pk>/ - Giveaway detail with entry form
"""

from django.urls import path
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

from .views import (GiveawayCreateView, GiveawayListView, GiveawayDetailView,
                  BusinessGiveawayListView, GiveawayEditView, WinnerSelectionStatusView,
                  GiveawayAnimationDataView, WinnerAnimationView)
from .permissions import is_member, can_enter_giveaway

app_name = 'giveaways'

# Apply security decorators to views that handle sensitive data
def secure_view(view_func):
    """Apply security decorators to sensitive views."""
    return never_cache(csrf_protect(view_func))

urlpatterns = [
    # ===== Offentlig oversikt over giveaways =====
    path(
        '', 
        GiveawayListView.as_view(), 
        name='list'
    ),
    
    # ===== Bedriftsoversikt over egne giveaways =====
    path(
        'business/', 
        login_required(secure_view(BusinessGiveawayListView.as_view())), 
        name='business-giveaways'
    ),
    
    # ===== Opprett ny giveaway (kun for bedrifter) =====
    path(
        'create/', 
        login_required(secure_view(GiveawayCreateView.as_view())), 
        name='giveaway-create'
    ),
    
    # ===== Detaljer og påmelding for giveaway =====
    path(
        '<int:pk>/', 
        secure_view(GiveawayDetailView.as_view()), 
        name='giveaway-detail'
    ),
    
    # ===== Rediger giveaway (kun for bedriftseiere) =====
    path(
        '<int:pk>/edit/', 
        login_required(secure_view(GiveawayEditView.as_view())), 
        name='giveaway-edit'
    ),
    
    # ===== Admin-only API for winner selection monitoring =====
    path(
        'admin/winner-status/', 
        WinnerSelectionStatusView.as_view(), 
        name='winner_selection_status'
    ),
    
    # ===== Winner selection animation views =====
    path(
        '<int:pk>/winner-animation/', 
        secure_view(WinnerAnimationView.as_view()), 
        name='winner-animation'
    ),
    
    # ===== API endpoint for animation data =====
    path(
        'api/animation-data/', 
        secure_view(GiveawayAnimationDataView.as_view()), 
        name='animation-data'
    ),
]

# Sikkerhetsmerknad:
# 1. Alle views som håndterer POST-data har CSRF-beskyttelse
# 2. Giveaway-opprettelse krever innlogging
# 3. Påmelding til giveaways er beskyttet med validering av lokasjon
# 4. Admin-API for vinnermonitorering er kun tilgjengelig for stab
