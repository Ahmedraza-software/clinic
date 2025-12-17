from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment


@receiver(post_save, sender=Appointment)
def update_financials_on_completion(sender, instance, created, **kwargs):
    """
    Signal to update financial data when appointment is completed.
    This provides an additional layer of reliability beyond the save method.
    """
    if not created and instance.status == 'completed':
        # Check if this was a status change to completed
        if hasattr(instance, '_state') and instance._state.adding is False:
            try:
                # Get the previous state from database
                old_instance = Appointment.objects.get(pk=instance.pk)
                if hasattr(old_instance, '_original_status'):
                    if old_instance._original_status != 'completed':
                        instance.update_doctor_financials()
            except Appointment.DoesNotExist:
                pass


@receiver(post_save, sender=Appointment)
def store_original_status(sender, instance, **kwargs):
    """Store the original status for comparison"""
    if instance.pk:
        try:
            original = Appointment.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Appointment.DoesNotExist:
            instance._original_status = None
