from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from doctors.models import Doctor
from patients.models import Patient

class Appointment(models.Model):
    """Model representing a doctor's appointment"""
    STATUS_CHOICES = (
        ('scheduled', _('Scheduled')),
        ('confirmed', _('Confirmed')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    )
    
    APPOINTMENT_TYPE_CHOICES = (
        ('consultation', _('Consultation')),
        ('follow_up', _('Follow-up')),
        ('routine_checkup', _('Routine Checkup')),
        ('emergency', _('Emergency')),
        ('other', _('Other')),
    )
    
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    
    # Appointment details
    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE_CHOICES,
        default='consultation'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    
    # Date and time
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    
    # Additional information
    reason = models.TextField(blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Payment information
    is_paid = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Cancellation fields
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_appointment_type_display()} - {self.patient.user.get_full_name() if hasattr(self.patient, 'user') else 'No Patient'} - {self.appointment_date}"
        
    def get_duration(self):
        """Calculate the duration of the appointment in minutes"""
        if not self.end_time or not self.appointment_time:
            return 0
            
        start = datetime.combine(self.appointment_date, self.appointment_time)
        end = datetime.combine(self.appointment_date, self.end_time)
        return (end - start).seconds // 60
        
    def is_upcoming(self):
        """Check if the appointment is in the future"""
        from django.utils import timezone
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            datetime.combine(self.appointment_date, self.appointment_time)
        )
        return appointment_datetime > now and self.status != 'cancelled'
    
    def save(self, *args, **kwargs):
        """Override save to update financial data when appointment is completed"""
        # Check if appointment status changed to completed
        old_status = None
        if self.pk:
            try:
                old_appointment = Appointment.objects.get(pk=self.pk)
                old_status = old_appointment.status
            except Appointment.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Trigger financial update if appointment was just completed
        if old_status != 'completed' and self.status == 'completed':
            self.update_doctor_financials()
    
    def update_doctor_financials(self):
        """Update doctor financial records when appointment is completed"""
        from patients.models import DoctorPayment, PatientPayment
        from decimal import Decimal
        from datetime import date, timedelta
        
        # Get current month
        today = date.today()
        current_month = today.replace(day=1)
        
        # Look for payments from this patient that mention this doctor or are around the appointment date
        doctor_name = self.doctor.user.get_full_name() if self.doctor.user else str(self.doctor)
        
        # First, look for payments that specifically mention this doctor in the notes
        doctor_specific_payments = PatientPayment.objects.filter(
            patient=self.patient,
            payment_date__gte=self.appointment_date - timedelta(days=30),  # Within a month
            payment_date__lte=self.appointment_date + timedelta(days=7),   # Up to 7 days after
            notes__icontains=doctor_name
        )
        
        # Also look for payments around the appointment date
        appointment_payments = PatientPayment.objects.filter(
            patient=self.patient,
            payment_date__gte=self.appointment_date - timedelta(days=7),
            payment_date__lte=self.appointment_date + timedelta(days=7),
            payment_type__in=['consultation_fee', 'appointment_fee']
        )
        
        # Combine both sets of payments (remove duplicates)
        all_payments = list(doctor_specific_payments) + list(appointment_payments)
        unique_payments = list({payment.id: payment for payment in all_payments}.values())
        
        # Calculate revenue from this appointment
        appointment_revenue = sum(payment.amount for payment in unique_payments)
        
        if appointment_revenue > 0:
            # Get or create DoctorPayment record for this month
            doctor_payment, created = DoctorPayment.objects.get_or_create(
                doctor=self.doctor,
                payment_period=current_month,
                defaults={
                    'revenue_generated': Decimal('0'),
                    'clinic_share': Decimal('0'),
                    'doctor_payout': Decimal('0'),
                    'is_paid': False
                }
            )
            
            # Only add revenue if this is a new appointment completion
            # (to avoid double-counting when appointment is saved multiple times)
            if not hasattr(self, '_financial_updated'):
                doctor_payment.revenue_generated += Decimal(str(appointment_revenue))
                doctor_payment.clinic_share = doctor_payment.revenue_generated * Decimal('0.20')
                doctor_payment.doctor_payout = doctor_payment.revenue_generated * Decimal('0.80')
                doctor_payment.save()
                
                # Mark as updated to prevent double-counting
                self._financial_updated = True
                
                print(f"Updated financials for Dr. {self.doctor}: +${appointment_revenue} revenue")
            else:
                print(f"Financial update skipped for Dr. {self.doctor} - already processed")
    
    class Meta:
        verbose_name = _('appointment')
        verbose_name_plural = _('appointments')
        ordering = ['-appointment_date', '-appointment_time']
        unique_together = ('doctor', 'appointment_date', 'appointment_time')

class Prescription(models.Model):
    """Model representing a prescription for a patient"""
    FREQUENCY_CHOICES = (
        ('od', _('Once daily')),
        ('bd', _('Twice daily')),
        ('tds', _('Three times daily')),
        ('qid', _('Four times daily')),
        ('q4h', _('Every 4 hours')),
        ('q6h', _('Every 6 hours')),
        ('q8h', _('Every 8 hours')),
        ('q12h', _('Every 12 hours')),
        ('q24h', _('Every 24 hours')),
        ('prn', _('As needed')),
        ('stat', _('Immediately')),
    )
    
    DURATION_UNIT_CHOICES = (
        ('day', _('Day(s)')),
        ('week', _('Week(s)')),
        ('month', _('Month(s)')),
        ('year', _('Year(s)')),
        ('until_finished', _('Until finished')),
        ('as_needed', _('As needed')),
    )
    
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        null=True,
        blank=True
    )
    
    # If prescription is created without an appointment
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    
    # Prescription details
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    duration = models.PositiveIntegerField()
    duration_unit = models.CharField(max_length=15, choices=DURATION_UNIT_CHOICES)
    instructions = models.TextField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    
    # Refill information
    refills_allowed = models.PositiveIntegerField(default=0)
    refills_remaining = models.PositiveIntegerField(default=0)
    
    # Additional information
    diagnosis = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.medication_name} - {self.patient}"
    
    def save(self, *args, **kwargs):
        # Set end_date based on duration and duration_unit if not set
        if not self.end_date and self.duration and self.duration_unit:
            from datetime import timedelta
            
            if self.duration_unit == 'day':
                delta = timedelta(days=self.duration)
            elif self.duration_unit == 'week':
                delta = timedelta(weeks=self.duration)
            elif self.duration_unit == 'month':
                # Approximate month as 30 days
                delta = timedelta(days=30 * self.duration)
            elif self.duration_unit == 'year':
                # Approximate year as 365 days
                delta = timedelta(days=365 * self.duration)
            else:
                delta = timedelta(days=0)
            
            self.end_date = self.start_date + delta
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('prescription')
        verbose_name_plural = _('prescriptions')
        ordering = ['-created_at']
