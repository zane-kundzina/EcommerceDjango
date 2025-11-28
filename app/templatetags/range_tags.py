from django import template

register = template.Library()

@register.filter
def times(value):
    try:
        value = int(float(value))  # handles SafeString, floats, decimals
    except (TypeError, ValueError):
        value = 0
    return range(value)

@register.filter
def minus(value, arg):
    try:
        value = int(float(value))
        arg = int(float(arg))
    except (TypeError, ValueError):
        return 0
    return value - arg
