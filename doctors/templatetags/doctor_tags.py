from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()

@register.filter(name='get_status_badge')
def get_status_badge(status):
    """
    Returns the appropriate badge class for appointment status.
    Usage: {{ appointment.status|get_status_badge }}
    """
    status_badges = {
        'scheduled': 'secondary',
        'confirmed': 'primary',
        'in_progress': 'info',
        'completed': 'success',
        'cancelled': 'danger',
        'no_show': 'dark',
    }
    return status_badges.get(status, 'secondary')

@register.filter(name='get_status_icon')
def get_status_icon(status):
    """
    Returns the appropriate icon for appointment status.
    Usage: {{ appointment.status|get_status_icon }}
    """
    status_icons = {
        'scheduled': 'far fa-calendar',
        'confirmed': 'fas fa-check-circle',
        'in_progress': 'fas fa-spinner fa-spin',
        'completed': 'fas fa-check-circle',
        'cancelled': 'fas fa-times-circle',
        'no_show': 'fas fa-user-slash',
    }
    return status_icons.get(status, 'far fa-question-circle')

@register.filter(name='get_status_color')
def get_status_color(status):
    """
    Returns the appropriate text color class for appointment status.
    Usage: {{ appointment.status|get_status_color }}
    """
    status_colors = {
        'scheduled': 'text-secondary',
        'confirmed': 'text-primary',
        'in_progress': 'text-info',
        'completed': 'text-success',
        'cancelled': 'text-danger',
        'no_show': 'text-dark',
    }
    return status_colors.get(status, 'text-secondary')

@register.filter(name='get_appointment_type_icon')
def get_appointment_type_icon(appointment_type):
    """
    Returns the appropriate icon for appointment type.
    Usage: {{ appointment.appointment_type|get_appointment_type_icon }}
    """
    type_icons = {
        'consultation': 'fas fa-stethoscope',
        'follow_up': 'fas fa-undo',
        'routine_checkup': 'fas fa-heartbeat',
        'emergency': 'fas fa-ambulance',
        'other': 'fas fa-calendar-alt',
    }
    return type_icons.get(appointment_type, 'far fa-calendar')

@register.filter(name='format_duration')
def format_duration(minutes):
    """
    Formats duration in minutes to a human-readable format.
    Usage: {{ appointment.duration|format_duration }}
    """
    if not minutes:
        return "N/A"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours} hour{'' if hours == 1 else 's'}"
    else:
        return f"{mins} minute{'' if mins == 1 else 's'}"

@register.filter(name='get_patient_initials')
def get_patient_initials(patient):
    """
    Returns the initials of a patient's name.
    Usage: {{ patient|get_patient_initials }}
    """
    if not patient or not hasattr(patient, 'user'):
        return "??"
    
    full_name = patient.user.get_full_name()
    if not full_name:
        return patient.user.username[:2].upper()
    
    parts = full_name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    elif full_name:
        return full_name[:2].upper()
    
    return "??"

@register.simple_tag
def get_status_choices():
    """
    Returns the status choices for filtering appointments.
    Usage: {% get_status_choices as status_choices %}
    """
    return [
        ('', _('All Status')),
        ('scheduled', _('Scheduled')),
        ('confirmed', _('Confirmed')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]

@register.filter(name='get_appointment_type_badge')
def get_appointment_type_badge(appointment_type):
    """
    Returns the appropriate badge class for appointment type.
    Usage: {{ appointment.appointment_type|get_appointment_type_badge }}
    """
    type_badges = {
        'consultation': 'bg-primary',
        'follow_up': 'bg-info',
        'routine_checkup': 'bg-success',
        'emergency': 'bg-danger',
        'other': 'bg-secondary',
    }
    return type_badges.get(appointment_type, 'bg-secondary')

@register.filter(name='get_appointment_type_text')
def get_appointment_type_text(appointment_type):
    """
    Returns the display text for appointment type.
    Usage: {{ appointment.appointment_type|get_appointment_type_text }}
    """
    type_texts = {
        'consultation': _('Consultation'),
        'follow_up': _('Follow Up'),
        'routine_checkup': _('Routine Checkup'),
        'emergency': _('Emergency'),
        'other': _('Other'),
    }
    return type_texts.get(appointment_type, _('Unknown'))
