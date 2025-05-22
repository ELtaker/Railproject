"""Admin configuration for the accounts app.

This module registers models from the accounts app to the Django admin interface
and customizes their presentation and functionality.

Classes:
    MemberProfileAdmin: Admin interface for MemberProfile model
    CustomUserAdmin: Enhanced admin interface for the User model
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth import get_user_model
from .models import MemberProfile
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Robust unregister
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "created_at")
    search_fields = ("user__email", "user__username", "city")
    list_select_related = ('user',)  # Reduce database queries
    date_hierarchy = 'created_at'    # Add date navigation
    list_filter = ('city',)
    readonly_fields = ('created_at',)

class CustomUserAdmin(DjangoUserAdmin):
    """Custom admin interface for the User model with optimized performance and better UI."""
    # Display email as the primary identifier
    list_display = ('email', 'username', 'first_name', 'last_name', 'city', 'is_staff', 'is_active', 'last_login')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'city')
    list_filter = DjangoUserAdmin.list_filter + ("groups", "is_active", "date_joined")
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('email',)
    date_hierarchy = 'date_joined'  # Add date navigation
    list_per_page = 25  # Control pagination for better performance
    
    # Add actions for bulk operations
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        """Admin action to make selected users active."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} brukere ble aktivert.')
    make_active.short_description = "Aktiver valgte brukere"
    
    def make_inactive(self, request, queryset):
        """Admin action to make selected users inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} brukere ble deaktivert.')
    make_inactive.short_description = "Deaktiver valgte brukere"

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personlig informasjon', {'fields': ('username', 'first_name', 'last_name', 'profile_image', 'city')}),
        ('Tillatelser', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Viktige datoer', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'profile_image', 'city', 'is_staff', 'is_active'),
        }),
    )

# Register the User model with our enhanced admin
admin.site.register(User, CustomUserAdmin)

# Register the MemberProfile model
admin.site.register(MemberProfile, MemberProfileAdmin)