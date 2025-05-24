from django.contrib import admin
from .models import Giveaway, Entry, Winner

import logging
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

logger = logging.getLogger(__name__)

@admin.register(Giveaway)
class GiveawayAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'business_name', 'get_location', 'status_badge', 'prize_value', 
        'entries_count', 'start_date', 'end_date', 'has_winner'
    )
    list_display_links = ('title',)
    list_select_related = ('business',)
    
    search_fields = ('title', 'business__name', 'description')
    list_filter = (
        'is_active', 'start_date', 'end_date', 'business__city',
        ('prize_value', admin.EmptyFieldListFilter)
    )
    date_hierarchy = 'created_at'
    
    readonly_fields = ('created_at', 'entries_count', 'status_display')
    
    fieldsets = (
        (_('Grunnleggende informasjon'), {
            'fields': ('title', 'description', 'business', 'image', 'prize_value', 'status_display')
        }),
        (_('Dato og aktivitet'), {
            'fields': ('start_date', 'end_date', 'is_active', 'created_at')
        }),
        (_('Spørsmål og svaralternativer'), {
            'fields': ('signup_question', 'signup_options')
        }),
        (_('Statistikk'), {
            'fields': ('entries_count',)
        }),
    )
    
    actions = ['mark_active', 'mark_inactive', 'export_entries', 'select_winner']
    
    def business_name(self, obj):
        """Display business name with link to business admin"""
        if obj.business:
            url = reverse('admin:businesses_business_change', args=[obj.business.id])
            return format_html('<a href="{}">{}</a>', url, obj.business.name)
        return '-'
        
    def get_location(self, obj):
        """Display business location (city) for the giveaway
        
        This helps admins see at a glance where each giveaway is located
        without changing the database structure, as location is stored
        on the related Business model.
        
        Args:
            obj: The Giveaway instance
            
        Returns:
            str: The business city or a placeholder if not available
        """
        if obj.business and obj.business.city:
            return obj.business.city
        return '-'
    get_location.short_description = _('Location')
    get_location.admin_order_field = 'business__city'
    business_name.short_description = _('Bedrift')
    business_name.admin_order_field = 'business__name'
    
    def status_badge(self, obj):
        """Display status with color-coded badge"""
        if not obj.is_active:
            return format_html('<span style="color: red;">✗ Inaktiv</span>')
        elif obj.is_expired():
            return format_html('<span style="color: orange;">⏰ Avsluttet</span>')
        elif obj.is_upcoming():
            return format_html('<span style="color: blue;">⏳ Kommende</span>')
        else:
            return format_html('<span style="color: green;">✓ Pågående</span>')
    status_badge.short_description = _('Status')
    
    def status_display(self, obj):
        """More detailed status for detail view"""
        if not obj.is_active:
            return _('Inaktiv (manuelt deaktivert)')
        elif obj.is_expired():
            return _('Avsluttet (etter sluttdato)')
        elif obj.is_upcoming():
            return _('Kommende (før startdato)')
        else:
            return _('Pågående (aktiv nå)')
    status_display.short_description = _('Detaljert status')
    
    def entries_count(self, obj):
        """Count entries with link to filtered entries admin"""
        count = obj.entries.count()
        if count:
            url = reverse('admin:giveaways_entry_changelist') + f'?giveaway__id__exact={obj.id}'
            return format_html('<a href="{}">{} deltakere</a>', url, count)
        return '0 deltakere'
    entries_count.short_description = _('Deltakere')
    
    def has_winner(self, obj):
        """Check if giveaway has a winner with link to winner admin"""
        try:
            winner = obj.winner
            url = reverse('admin:giveaways_winner_change', args=[winner.id])
            return format_html('<a href="{}" style="color: green;">Ja - {}</a>', url, winner.user.email)
        except (Winner.DoesNotExist, AttributeError):
            return format_html('<span style="color: gray;">Nei</span>')
    has_winner.short_description = _('Vinner')
    has_winner.boolean = False  # Changed to False to avoid using boolean icons
    
    def mark_active(self, request, queryset):
        """Mark selected giveaways as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} giveaways marked as active.')
    mark_active.short_description = _('Merk som aktive')
    
    def mark_inactive(self, request, queryset):
        """Mark selected giveaways as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} giveaways marked as inactive.')
    mark_inactive.short_description = _('Merk som inaktive')
    
    def export_entries(self, request, queryset):
        """Export entries for selected giveaways to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="giveaway_entries.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Giveaway', 'User Email', 'Answer', 'Location', 'Entry Date'])
        
        for giveaway in queryset:
            entries = giveaway.entries.select_related('user').all()
            for entry in entries:
                writer.writerow([
                    giveaway.title,
                    entry.user.email,
                    entry.answer,
                    entry.user_location_city,
                    entry.entered_at.strftime('%Y-%m-%d %H:%M')
                ])
                
        return response
    export_entries.short_description = _('Eksportér deltakere til CSV')
    
    def select_winner(self, request, queryset):
        """
        Admin action to select a winner for the selected giveaways.
        Only works for expired giveaways without existing winners.
        Uses the scalable winner selection system.
        """
        from django.urls import reverse
        from django.utils.html import mark_safe
        from .tasks import select_winners_batch
        from .services.winner_selection import find_eligible_giveaways
        
        # Filter for eligible giveaways
        from django.utils import timezone
        now = timezone.now()
        
        # Count all selected giveaways
        total_count = queryset.count()
        
        # Filter for eligible giveaways only
        eligible_giveaways = queryset.filter(end_date__lt=now, is_active=True)
        eligible_ids = list(eligible_giveaways.values_list('id', flat=True))
        
        # Find which ones already have winners
        from .models import Winner
        existing_winners = Winner.objects.filter(giveaway__in=eligible_giveaways).values_list('giveaway_id', flat=True)
        existing_winners = list(existing_winners)
        
        # Get final list of eligible giveaways without winners
        final_eligible_ids = [gid for gid in eligible_ids if gid not in existing_winners]
        
        # Create summary counts
        not_expired_count = total_count - len(eligible_ids)
        has_winner_count = len(existing_winners)
        eligible_count = len(final_eligible_ids)
        
        if eligible_count == 0:
            # No eligible giveaways
            message_parts = []
            if not_expired_count > 0:
                message_parts.append(f"{not_expired_count} ikke utløpt")
            if has_winner_count > 0:
                message_parts.append(f"{has_winner_count} har allerede vinner")
                
            reason = " og ".join(message_parts) if message_parts else "ukjent årsak"
            
            self.message_user(
                request,
                _(f'Ingen kvalifiserte giveaways å trekke vinnere for ({reason}).'),
                level='warning'
            )
            return
        
        # Check for large batches
        batch_size = 100  # Default chunk size
        if eligible_count > 200:
            self.message_user(
                request,
                _(f'Starter trekning av vinnere for {eligible_count} giveaways. Dette kan ta litt tid.'),
                level='warning'
            )
        
        # Start the asynchronous batch task
        result = select_winners_batch.delay(final_eligible_ids, batch_size)
        task_id = result.task_id
        
        # Provide feedback with a link to check status
        status_url = reverse('admin:winner_selection_status') + f'?task_id={task_id}'
        
        self.message_user(
            request,
            mark_safe(_(
                f'Trekning av vinnere startet for {eligible_count} giveaways. '
                f'<a href="{status_url}" target="_blank" class="winner-status-link">Sjekk status</a>. '
                f'<small>({not_expired_count} ikke utløpt, {has_winner_count} har allerede vinner)</small>'
            )),
            level='success'
        )
    
    select_winner.short_description = _('Trekk vinner for valgte giveaways')

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Entry model.
    Provides enhanced display, filtering, and functionality.
    """
    list_display = (
        'user_email', 'giveaway_title', 'answer_display', 
        'user_location_city', 'entered_at'
    )
    list_display_links = ('user_email',)
    list_select_related = ('giveaway', 'user')
    
    search_fields = (
        'giveaway__title', 'user__email', 
        'user__username', 'user_location_city'
    )
    list_filter = (
        'entered_at', 'user_location_city',
        ('giveaway', admin.RelatedOnlyFieldListFilter)
    )
    date_hierarchy = 'entered_at'
    
    readonly_fields = ('entered_at', 'is_correct')
    
    def user_email(self, obj):
        """Display user email with link to user admin"""
        if obj.user:
            # Get the app label and model name dynamically to build the correct URL
            app_label = obj.user._meta.app_label
            model_name = obj.user._meta.model_name
            url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_email.short_description = _('Bruker')
    user_email.admin_order_field = 'user__email'
    
    def giveaway_title(self, obj):
        """Display giveaway title with link to giveaway admin"""
        if obj.giveaway:
            url = reverse('admin:giveaways_giveaway_change', args=[obj.giveaway.id])
            return format_html('<a href="{}">{}</a>', url, obj.giveaway.title)
        return '-'
    giveaway_title.short_description = _('Giveaway')
    giveaway_title.admin_order_field = 'giveaway__title'
    
    def answer_display(self, obj):
        """Display answer with correct/incorrect indicator"""
        if obj.is_correct_answer():
            return format_html('<span style="color: green;">{} &#10003;</span>', obj.answer)
        return format_html('<span style="color: red;">{} &#10007;</span>', obj.answer)
    answer_display.short_description = _('Svar')
    
    def is_correct(self, obj):
        """Display whether answer is correct"""
        return obj.is_correct_answer()
    is_correct.short_description = _('Korrekt svar')
    is_correct.boolean = True


@admin.register(Winner)
class WinnerAdmin(admin.ModelAdmin):
    """
    Admin configuration for Winner model.
    Provides enhanced display, filtering, and functionality.
    """
    list_display = (
        'user_email', 'giveaway_title', 'was_correct_answer_display',
        'selected_at', 'notification_status'
    )
    list_display_links = ('user_email',)
    list_select_related = ('giveaway', 'user')
    
    search_fields = ('giveaway__title', 'user__email', 'user__username')
    list_filter = ('selected_at', 'notification_sent')
    date_hierarchy = 'selected_at'
    
    readonly_fields = ('selected_at', 'was_correct_answer_display', 'entry_details')
    
    actions = ['mark_notification_sent']
    
    def user_email(self, obj):
        """Display user email with link to user admin"""
        if obj.user:
            # Get the app label and model name dynamically to build the correct URL
            app_label = obj.user._meta.app_label
            model_name = obj.user._meta.model_name
            url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_email.short_description = _('Bruker')
    user_email.admin_order_field = 'user__email'
    
    def giveaway_title(self, obj):
        """Display giveaway title with link to giveaway admin"""
        if obj.giveaway:
            url = reverse('admin:giveaways_giveaway_change', args=[obj.giveaway.id])
            return format_html('<a href="{}">{}</a>', url, obj.giveaway.title)
        return '-'
    giveaway_title.short_description = _('Giveaway')
    giveaway_title.admin_order_field = 'giveaway__title'
    
    def was_correct_answer_display(self, obj):
        """Display whether winner had correct answer"""
        if obj.was_correct_answer():
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    was_correct_answer_display.short_description = _('Korrekt svar')
    # Removed boolean=True to fix admin display error
    
    def notification_status(self, obj):
        """Display notification status"""
        if obj.notification_sent:
            return format_html('<span style="color: green;">Sendt ✓</span>')
        return format_html('<span style="color: orange;">Venter ⏳</span>')
    notification_status.short_description = _('Varsling')
    
    def entry_details(self, obj):
        """Display entry details"""
        entry = obj.get_entry()
        if entry:
            url = reverse('admin:giveaways_entry_change', args=[entry.id])
            return format_html(
                '<a href="{}">Se detaljer</a><br>Svar: {}<br>Lokasjon: {}<br>Tidspunkt: {}',
                url, entry.answer, entry.user_location_city, entry.entered_at
            )
        return 'Ingen deltakerdetaljer funnet'
    entry_details.short_description = _('Deltakerdetaljer')
    
    def mark_notification_sent(self, request, queryset):
        """Mark notifications as sent for selected winners"""
        for winner in queryset:
            winner.mark_notification_sent()
        self.message_user(request, f'Marked notifications as sent for {queryset.count()} winners.')
    mark_notification_sent.short_description = _('Merk varslinger som sendt')