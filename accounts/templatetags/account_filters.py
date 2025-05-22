# In accounts/templatetags/account_filters.py
from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def split(value, sep):
    """
    Split a string into a list using the given separator.
    Transforms each item into a dictionary with 'name' and 'label' keys.
    
    Usage: {{ "item1,item2,item3"|split:"," }}
    Returns: [{'name': 'item1', 'label': 'Item1'}, ...]
    """
    if not value:
        return []
    
    return [{'name': item.strip(), 'label': item.strip().capitalize()} 
            for item in value.split(sep)]

@register.filter
def format_datetime_since(value):
    """
    Format a datetime as a human-readable 'time since' string in Norwegian.
    
    Usage: {{ some_datetime|format_datetime_since }}
    Returns: 'for 3 dager siden', 'for 5 minutter siden', etc.
    """
    if not value:
        return ''
        
    now = datetime.now()
    if hasattr(value, 'tzinfo') and value.tzinfo:
        now = datetime.now(value.tzinfo)
        
    diff = now - value
    
    if diff < timedelta(minutes=1):
        return 'nettopp'
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f'for {minutes} {"minutt" if minutes == 1 else "minutter"} siden'
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f'for {hours} {"time" if hours == 1 else "timer"} siden'
    elif diff < timedelta(days=30):
        days = diff.days
        return f'for {days} {"dag" if days == 1 else "dager"} siden'
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f'for {months} {"måned" if months == 1 else "måneder"} siden'
    else:
        years = diff.days // 365
        return f'for {years} {"år" if years == 1 else "år"} siden'

@register.simple_tag
def active_link(request, pattern):
    """
    Return 'active' if the current URL matches the pattern.
    Useful for highlighting active navigation items.
    
    Usage: {% active_link request 'accounts:member-profile' %}
    Returns: 'active' if current URL matches the pattern, '' otherwise
    """
    import re
    if re.search(pattern, request.path):
        return 'active'
    return ''