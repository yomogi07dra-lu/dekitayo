from django import template

register = template.Library()

@register.filter
def index(list_value, i):
    try:
        return list_value[i]
    except:
        return ''