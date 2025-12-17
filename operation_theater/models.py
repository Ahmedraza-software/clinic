from django.db import models
from django.contrib.auth import get_user_model
from patients.models import Patient
from doctors.models import Doctor

User = get_user_model()

class SurgeryType(models.Model):
    """Model for different types of surgeries/procedures."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration = models.DurationField(help_text="Estimated duration of the surgery")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Surgery Types"
        ordering = ['name']

class OperationTheater(models.Model):
    """Model for operation theaters."""
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200, blank=True)
    is_available = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    supervising_doctors = models.ManyToManyField(
        Doctor,
        blank=True,
        related_name='supervised_operation_theaters',
        help_text='Doctors who supervise this operation theater.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Surgery(models.Model):
    """Model for scheduling surgeries."""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='surgeries')
    surgeon = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='surgeries')
    surgery_type = models.ForeignKey(SurgeryType, on_delete=models.PROTECT, null=True, blank=True)
    operation_theater = models.ForeignKey(OperationTheater, on_delete=models.PROTECT)
    scheduled_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_surgeries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        surgery_type_name = self.surgery_type.name if self.surgery_type else "General Surgery"
        return f"{self.patient.user.get_full_name()} - {surgery_type_name} - {self.scheduled_date}"

    class Meta:
        verbose_name_plural = "Surgeries"
        ordering = ['-scheduled_date', '-start_time']

class SurgeryConsumable(models.Model):
    """Model to track consumables used in surgeries."""
    surgery = models.ForeignKey(Surgery, on_delete=models.CASCADE, related_name='consumables')
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=50, default='pcs')
    notes = models.TextField(blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} x{self.quantity} {self.unit} - {self.surgery}"

    class Meta:
        ordering = ['-used_at']

class SurgeryTeam(models.Model):
    """Model to track the team members involved in a surgery."""
    ROLE_CHOICES = [
        ('surgeon', 'Surgeon'),
        ('assistant', 'Assistant Surgeon'),
        ('anesthetist', 'Anesthetist'),
        ('nurse', 'Scrub Nurse'),
        ('technician', 'Surgical Technician'),
        ('other', 'Other'),
    ]

    surgery = models.ForeignKey(Surgery, on_delete=models.CASCADE, related_name='team_members')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='surgery_teams')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    notes = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False, help_text="Primary surgeon for the procedure")

    def __str__(self):
        return f"{self.doctor.user.get_full_name()} - {self.get_role_display()} - {self.surgery}"

    class Meta:
        verbose_name_plural = "Surgery Teams"
        unique_together = ('surgery', 'doctor')
        ordering = ['-is_primary', 'role', 'doctor__user__first_name']
