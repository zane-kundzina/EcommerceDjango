from django import template

register = template.Library()

@register.filter
def times(number):
    return range(number)

@register.filter
def minus(value, arg):
    return value - arg