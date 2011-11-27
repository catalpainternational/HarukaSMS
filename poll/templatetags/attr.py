from django import template

def attr(input, property):
    return input.__getattribute__(property)

register = template.Library()
register.filter('attr', attr)
