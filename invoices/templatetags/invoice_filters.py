from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """Return the absolute value of the argument."""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return 0
