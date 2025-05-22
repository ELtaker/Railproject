import logging
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Business

logger = logging.getLogger(__name__)

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Business model.
    Provides enhanced display, search, filtering, and functionality.
    """
    list_display = (
        'name', 'city', 'organization_number', 'display_contact',
        'user_email', 'display_website', 'created_at', 'display_profile_completeness'
    )
    list_display_links = ('name',)
    list_select_related = ('user', 'admin')
    search_fields = (
        'name', 'user__email', 'admin__email', 'city', 
        'postal_code', 'organization_number', 'contact_person'
    )
    list_filter = (
        'created_at', 'city', ('logo', admin.EmptyFieldListFilter),
        ('website', admin.EmptyFieldListFilter)
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (_('Grunnleggende informasjon'), {
            'fields': ('name', 'organization_number', 'description', 'logo')
        }),
        (_('Kontaktinformasjon'), {
            'fields': ('address', 'postal_code', 'city', 'phone', 'website', 'contact_person', 'social_media')
        }),
        (_('Brukerkonto'), {
            'fields': ('user', 'admin', 'created_at')
        }),
    )
    
    actions = ['export_businesses_csv']
    
    def display_contact(self, obj):
        """
        Display phone and contact person in admin list view.
        """
        phone = obj.phone or '-'
        contact = obj.contact_person or '-'
        return f"{contact} ({phone})"
    display_contact.short_description = _('Kontakt')
    
    def user_email(self, obj):
        """
        Display user email in admin list view.
        """
        return obj.user.email
    user_email.short_description = _('Epost')
    user_email.admin_order_field = 'user__email'
    
    def display_website(self, obj):
        """
        Display website as a clickable link.
        """
        if obj.website:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.website, obj.website)
        return '-'
    display_website.short_description = _('Nettside')
    
    def display_profile_completeness(self, obj):
        """
        Display a visual indicator of profile completeness.
        """
        if obj.has_complete_profile():
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: orange;">⚠</span>')
    display_profile_completeness.short_description = _('Komplett profil')
    
    def export_businesses_csv(self, request, queryset):
        """
        Export selected businesses to CSV.
        """
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="businesses.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'City', 'Contact', 'Email', 'Website'])
        
        for business in queryset:
            writer.writerow([
                business.name,
                business.city,
                business.contact_person or '',
                business.user.email,
                business.website or ''
            ])
            
        return response
    export_businesses_csv.short_description = _('Eksportér valgte bedrifter til CSV')