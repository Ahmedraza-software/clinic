from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class Medicine(models.Model):
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    manufacturer = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=50, default='tablet')
    strength = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.strength:
            return f"{self.name} ({self.strength})"
        return self.name

class Prescription(models.Model):
    FREQUENCY_CHOICES = [
        ('OD', 'Once Daily'),
        ('BID', 'Twice Daily'),
        ('TID', 'Three Times Daily'),
        ('QID', 'Four Times Daily'),
        ('QHS', 'At Bedtime'),
        ('Q4H', 'Every 4 Hours'),
        ('Q6H', 'Every 6 Hours'),
        ('Q8H', 'Every 8 Hours'),
        ('PRN', 'As Needed'),
    ]

    DURATION_UNIT_CHOICES = [
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('indefinite', 'Until Further Notice'),
    ]

    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='medicine_prescriptions')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='prescribed_medicines')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100, help_text='e.g., 1 tablet, 5ml, etc.')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    duration = models.PositiveIntegerField(help_text='Duration of treatment')
    duration_unit = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, default='days')
    instructions = models.TextField(blank=True, null=True, help_text='Special instructions')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.end_date and self.duration and self.start_date:
            from datetime import timedelta
            if self.duration_unit == 'days':
                self.end_date = self.start_date + timedelta(days=self.duration)
            elif self.duration_unit == 'weeks':
                self.end_date = self.start_date + timedelta(weeks=self.duration)
            elif self.duration_unit == 'months':
                # Approximate month as 30 days
                self.end_date = self.start_date + timedelta(days=self.duration * 30)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medicine.name} for {self.patient.user.get_full_name()} - {self.get_frequency_display()}"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=10, choices=Prescription.FREQUENCY_CHOICES)
    duration = models.PositiveIntegerField()
    duration_unit = models.CharField(max_length=10, choices=Prescription.DURATION_UNIT_CHOICES)
    instructions = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(help_text='Number of units to dispense')
    refill_allowed = models.BooleanField(default=False)
    refill_times = models.PositiveIntegerField(default=0, help_text='Number of refills allowed')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.medicine.name} - {self.dosage} {self.get_frequency_display()}"
