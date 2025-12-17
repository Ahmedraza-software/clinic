from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS class(es) to a form field widget when rendering."""
    if not hasattr(field, 'field'):
        return field
    widget = field.field.widget
    existing = widget.attrs.get('class', '')
    combined = (existing + ' ' + (css_class or '')).strip()
    attrs = dict(widget.attrs)
    attrs['class'] = combined
    return field.as_widget(attrs=attrs)

@register.filter(name='attr')
def set_attr(field, arg):
    """Set a single attribute on a widget during render. Usage: {{ field|attr:"placeholder:Text" }}"""
    if not hasattr(field, 'field'):
        return field
    try:
        key, value = (arg or '').split(':', 1)
    except ValueError:
        return field
    attrs = dict(field.field.widget.attrs)
    attrs[key] = value
    return field.as_widget(attrs=attrs)
