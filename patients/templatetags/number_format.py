from django import template

register = template.Library()

@register.filter
def abbreviate_number(value):
    """
    Convert numbers to abbreviated format:
    1000 -> 1k
    1500 -> 1.5k
    1000000 -> 1M
    1500000 -> 1.5M
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    
    if value >= 1000000:
        # Millions
        result = value / 1000000
        if result == int(result):
            return f"{int(result)}M"
        else:
            return f"{result:.1f}M"
    elif value >= 1000:
        # Thousands
        result = value / 1000
        if result == int(result):
            return f"{int(result)}k"
        else:
            return f"{result:.1f}k"
    else:
        # Less than 1000
        if value == int(value):
            return str(int(value))
        else:
            return f"{value:.1f}"
