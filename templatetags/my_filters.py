from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def index(value, arg):
    """
    Returns the value at the specified index in a list or iterable.
    Usage: {{ my_list|index:0 }} returns first element of my_list
    """
    try:
        return value[arg]
    except (IndexError, TypeError, KeyError):
        return ""
