from django import template

register = template.Library()

@register.filter
def list_item(lst, i):
    try:
        return lst[i]
    except:
        return None

@register.filter
def dict_value(dict, key):
    return dict[key]

@register.filter
def mult(value, arg):
    return int(value) * int(arg)