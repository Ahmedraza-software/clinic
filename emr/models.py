from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# Import the Patient model from the patients app
from patients.models import Patient

class PatientMedicalRecord(models.Model):
    """Electronic Medical Record for patients"""
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_record'
    )
    blood_type = models.CharField(max_length=10, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    family_history = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical Record - {self.patient.user.get_full_name() or self.patient.user.email}"

class VitalSigns(models.Model):
    """Model to track patient vital signs over time"""
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='vital_signs'
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_vitals'
    )
    temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text="Temperature in °C")
    blood_pressure_systolic = models.PositiveSmallIntegerField(help_text="Systolic blood pressure (mmHg)")
    blood_pressure_diastolic = models.PositiveSmallIntegerField(help_text="Diastolic blood pressure (mmHg)")
    heart_rate = models.PositiveSmallIntegerField(help_text="Heart rate (bpm)")
    respiratory_rate = models.PositiveSmallIntegerField(help_text="Breaths per minute")
    oxygen_saturation = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="SpO2 (%)"
    )
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    height = models.DecimalField(max_digits=5, decimal_places=2, help_text="Height in cm")
    notes = models.TextField(blank=True, null=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Vital Signs"
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Vitals for {self.patient} at {self.recorded_at}"

class DigitalFormTemplate(models.Model):
    """Template for digital forms that can be filled out"""
    FORM_TYPES = [
        ('consent', 'Consent Form'),
        ('medical_history', 'Medical History'),
        ('surgical', 'Surgical Checklist'),
        ('admission', 'Admission Form'),
        ('discharge', 'Discharge Summary'),
        ('custom', 'Custom Form'),
    ]

    name = models.CharField(max_length=200)
    form_type = models.CharField(max_length=50, choices=FORM_TYPES)
    description = models.TextField(blank=True, null=True)
    content = models.JSONField()  # Stores the form schema/definition
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_form_type_display()}: {self.name}"

class FilledForm(models.Model):
    """Instance of a filled out form"""
    template = models.ForeignKey(DigitalFormTemplate, on_delete=models.PROTECT)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='filled_forms'
    )
    filled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='user_filled_forms'
    )
    form_data = models.JSONField()  # Stores the actual form responses
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.template.name} - {self.patient} - {self.created_at.date()}"

class Equipment(models.Model):
    """Medical equipment tracking"""
    EQUIPMENT_TYPES = [
        ('monitor', 'Patient Monitor'),
        ('ventilator', 'Ventilator'),
        ('ultrasound', 'Ultrasound Machine'),
        ('defibrillator', 'Defibrillator'),
        ('anesthesia', 'Anesthesia Machine'),
        ('surgical', 'Surgical Equipment'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
    ]

    name = models.CharField(max_length=200)
    equipment_type = models.CharField(max_length=50, choices=EQUIPMENT_TYPES)
    model_number = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    rfid_tag = models.CharField(max_length=100, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    location = models.CharField(max_length=200, blank=True, null=True)
    last_maintenance = models.DateField(blank=True, null=True)
    next_maintenance = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Equipment"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()}) - {self.serial_number or 'No Serial'}"

class EquipmentCheckout(models.Model):
    """Track equipment check-in/check-out"""
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name='checkouts')
    checked_out_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='equipment_checkouts'
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment_usage'
    )
    checkout_time = models.DateTimeField(default=timezone.now)
    expected_return = models.DateTimeField(blank=True, null=True)
    return_time = models.DateTimeField(blank=True, null=True)
    condition_out = models.TextField(blank=True, null=True)
    condition_in = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def is_overdue(self):
        if self.return_time:
            return False
        if self.expected_return:
            return timezone.now() > self.expected_return
        return False

    def __str__(self):
        return f"{self.equipment} - Checked out: {self.checkout_time}"

class AlertRule(models.Model):
    """Rules for generating alerts based on vital signs or other conditions"""
    ALERT_TYPES = [
        ('vital_high', 'Vital Sign High'),
        ('vital_low', 'Vital Sign Low'),
        ('form_incomplete', 'Form Incomplete'),
        ('equipment_due', 'Equipment Due for Maintenance'),
        ('medication_due', 'Medication Due'),
    ]

    name = models.CharField(max_length=200)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    is_active = models.BooleanField(default=True)
    condition = models.JSONField(help_text="JSON structure defining the alert condition")
    message_template = models.TextField(help_text="Alert message template")
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.name}"

class Alert(models.Model):
    """Generated alerts based on rules"""
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='alerts')
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    message = models.TextField()
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rule.name} - {self.message[:50]}..."

class ReportTemplate(models.Model):
    """Templates for automated reports"""
    REPORT_TYPES = [
        ('daily_rounds', 'Daily Rounds'),
        ('surgical', 'Surgical Report'),
        ('discharge', 'Discharge Summary'),
        ('billing', 'Billing Report'),
        ('inventory', 'Inventory Report'),
        ('custom', 'Custom Report'),
    ]

    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    description = models.TextField(blank=True, null=True)
    template = models.TextField(help_text="Report template (can use template language)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_report_type_display()}: {self.name}"

class GeneratedReport(models.Model):
    """Generated reports based on templates"""
    template = models.ForeignKey(ReportTemplate, on_delete=models.PROTECT)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports'
    )
    parameters = models.JSONField(help_text="Parameters used to generate the report")
    report_content = models.TextField(help_text="The actual generated report content")
    file = models.FileField(upload_to='reports/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.template.name} - {self.created_at.date()}"

class MedicalHistoryRecord(models.Model):
    """Individual medical history records for patients"""
    RECORD_TYPES = [
        ('consultation', 'Consultation'),
        ('lab_test', 'Lab Test'),
        ('procedure', 'Procedure'),
        ('surgery', 'Surgery'),
        ('emergency', 'Emergency Visit'),
        ('follow_up', 'Follow-up'),
        ('vaccination', 'Vaccination'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_history_records'
    )
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_records'
    )
    doctor_name = models.CharField(max_length=200, help_text="Doctor name for display")
    diagnosis = models.TextField()
    treatment = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Medical History Record'
        verbose_name_plural = 'Medical History Records'
    
    def __str__(self):
        return f"{self.patient} - {self.get_record_type_display()} - {self.date}"

class PatientAllergy(models.Model):
    """Patient allergies"""
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('life_threatening', 'Life Threatening'),
    ]
    
    ALLERGY_TYPES = [
        ('drug', 'Drug/Medication'),
        ('food', 'Food'),
        ('environmental', 'Environmental'),
        ('contact', 'Contact'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='allergies_detailed'
    )
    allergen = models.CharField(max_length=200)
    allergy_type = models.CharField(max_length=20, choices=ALLERGY_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    reaction = models.TextField(help_text="Description of allergic reaction")
    date_identified = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-severity', 'allergen']
        verbose_name = 'Patient Allergy'
        verbose_name_plural = 'Patient Allergies'
    
    def __str__(self):
        return f"{self.patient} - {self.allergen} ({self.get_severity_display()})"

class PatientMedication(models.Model):
    """Current medications for patients"""
    FREQUENCY_CHOICES = [
        ('once_daily', 'Once daily'),
        ('twice_daily', 'Twice daily'),
        ('three_times_daily', 'Three times daily'),
        ('four_times_daily', 'Four times daily'),
        ('as_needed', 'As needed'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('discontinued', 'Discontinued'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='current_medications_detailed'
    )
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    route = models.CharField(max_length=50, default='Oral')  # Oral, IV, IM, etc.
    indication = models.TextField(help_text="What condition this medication treats")
    prescribed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescribed_medications'
    )
    prescribed_by_name = models.CharField(max_length=200, help_text="Prescribing doctor name")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date', 'medication_name']
        verbose_name = 'Patient Medication'
        verbose_name_plural = 'Patient Medications'
    
    def __str__(self):
        return f"{self.patient} - {self.medication_name} {self.dosage}"
