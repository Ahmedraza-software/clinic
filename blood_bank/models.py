from django.db import models
from django.utils import timezone

class Donor(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    DONATION_TYPE_CHOICES = [
        ('whole', 'Whole Blood'),
        ('plasma', 'Plasma'),
        ('platelets', 'Platelets'),
        ('double_red', 'Double Red Cells'),
    ]
    
    # Personal Information
    full_name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    
    # Medical Information
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    weight = models.DecimalField(max_digits=5, decimal_places=1)  # kg
    donation_count = models.IntegerField(default=0)
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, default='whole')
    
    # Current Donation
    donation_date = models.DateField(default=timezone.now)
    donation_time = models.TimeField(default=timezone.now)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    medical_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-registered_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.blood_group})"
    
    @property
    def blood_units(self):
        """Return the number of blood units this donor contributes"""
        return 1  # Each donation contributes 1 unit

class BloodTransfer(models.Model):
    """Model for tracking blood unit transfers to patients"""
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    # Patient Information
    patient_name = models.CharField(max_length=100)
    patient_id = models.CharField(max_length=50)
    blood_type = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    units = models.IntegerField()
    
    # Transfer Details
    transfer_date = models.DateField()
    transfer_time = models.TimeField()
    
    # Doctor Information
    doctor_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_emergency = models.BooleanField(default=False)
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient_name} - {self.blood_type} ({self.units} units)"
