from django.contrib import admin
from .models import Giveaway, Entry, Winner

@admin.register(Giveaway)
class GiveawayAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'start_date', 'end_date', 'is_active')
    search_fields = ('title', 'business__name')
    list_filter = ('is_active', 'start_date', 'end_date')

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('giveaway', 'user', 'entered_at')
    search_fields = ('giveaway__title', 'user__email')

@admin.register(Winner)
class WinnerAdmin(admin.ModelAdmin):
    list_display = ('giveaway', 'user', 'selected_at')
    search_fields = ('giveaway__title', 'user__email')