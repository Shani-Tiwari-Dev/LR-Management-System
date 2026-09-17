from django import template

register = template.Library()


@register.filter
def get(mapping, key):
    """Look up a dictionary key that contains spaces, e.g. record|get:"Bill No"."""
    try:
        return mapping.get(key, "")
    except AttributeError:
        return ""
