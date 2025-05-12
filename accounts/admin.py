from django.contrib import admin
from .models import User, Company

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'city', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'city')
    list_filter = ('is_staff', 'is_active')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 'email', 'organization_number', 'is_active', 'is_staff', 'is_superuser', 'date_joined'
    )
    search_fields = ('company_name', 'email', 'organization_number')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'city')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('company_name', 'organization_number', 'email', 'password')}),
        ('Kontaktperson', {'fields': ('first_name', 'last_name', 'address', 'postal_code', 'city')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined',)}),
    )
    filter_horizontal = ('groups', 'user_permissions')