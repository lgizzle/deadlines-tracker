from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def in_dict(dictionary, key):
    """Check if a key exists in a dictionary."""
    if dictionary is None:
        return False
    return key in dictionary
