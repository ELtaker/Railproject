from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth import get_user_model
from .models import MemberProfile

User = get_user_model()

# Robust unregister
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "created_at")
    search_fields = ("user__email", "city")

class CustomUserAdmin(DjangoUserAdmin):
    list_display = ('email', 'username', 'city', 'is_staff', 'is_active', 'last_login')
    search_fields = ('email', 'username', 'city')
    list_filter = DjangoUserAdmin.list_filter + ("groups",)
    readonly_fields = ('last_login',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(MemberProfile, MemberProfileAdmin)