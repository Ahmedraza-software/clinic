from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Patient(models.Model):
    """Model representing a patient in the clinic"""
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    
    # Personal Information
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, help_text=_("Height in cm"), blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text=_("Weight in kg"), blank=True, null=True)
    
    # Contact Information
    phone = models.CharField(max_length=15, blank=True, null=True, help_text=_("Patient's phone number"))
    address = models.TextField(blank=True, null=True, help_text=_("Patient's address"))
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True, null=True)
    
    # Medical Information
    allergies = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    past_medical_history = models.TextField(blank=True, null=True)
    family_medical_history = models.TextField(blank=True, null=True)
    
    # Additional Information
    occupation = models.CharField(max_length=100, blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('discharged', 'Discharged'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def age(self):
        import datetime
        today = datetime.date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def has_medical_history(self):
        """Check if patient has any medical history records"""
        return (
            hasattr(self, 'medical_history_records') and self.medical_history_records.exists()
        ) or (
            hasattr(self, 'allergies_detailed') and self.allergies_detailed.filter(is_active=True).exists()
        ) or (
            hasattr(self, 'current_medications_detailed') and self.current_medications_detailed.filter(status='active').exists()
        )
    
    class Meta:
        verbose_name = _('patient')
        verbose_name_plural = _('patients')
        ordering = ['-created_at']

class PatientDocument(models.Model):
    """Model for storing patient documents like reports, prescriptions, etc."""
    DOCUMENT_TYPES = (
        ('prescription', _('Prescription')),
        ('report', _('Medical Report')),
        ('scan', _('Scan Report')),
        ('lab', _('Lab Report')),
        ('other', _('Other')),
    )
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='patient_documents/')
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.patient}"
    
    class Meta:
        verbose_name = _('patient document')
        verbose_name_plural = _('patient documents')
        ordering = ['-uploaded_at']

class PatientPayment(models.Model):
    """Model for storing patient payment records"""
    PAYMENT_METHODS = (
        ('cash', _('Cash')),
        ('card', _('Credit/Debit Card')),
        ('bank_transfer', _('Bank Transfer')),
        ('insurance', _('Insurance')),
    )
    
    PAYMENT_TYPES = (
        ('registration', _('Registration Fee')),
        ('consultation', _('Consultation Fee')),
        ('procedure', _('Procedure Fee')),
        ('medication', _('Medication')),
        ('discharge', _('Discharge Payment')),
        ('bill_payment', _('Bill Payment')),
        ('other', _('Other')),
    )
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='registration')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('patient payment')
        verbose_name_plural = _('patient payments')
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.patient.full_name} - ${self.amount} ({self.get_payment_type_display()})"


class PatientBill(models.Model):
    """Model for tracking patient bills and dues"""
    
    BILL_STATUS_CHOICES = (
        ('unpaid', _('Unpaid')),
        ('partially_paid', _('Partially Paid')),
        ('paid', _('Paid')),
    )
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='bills'
    )
    bill_number = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=BILL_STATUS_CHOICES, default='unpaid')
    bill_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bills'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('patient bill')
        verbose_name_plural = _('patient bills')
        ordering = ['-bill_date']
    
    def __str__(self):
        return f"{self.bill_number} - {self.patient.full_name} - ${self.amount}"
    
    @property
    def remaining_amount(self):
        from decimal import Decimal
        amount = self.amount if isinstance(self.amount, Decimal) else Decimal(str(self.amount))
        paid = self.paid_amount if isinstance(self.paid_amount, Decimal) else Decimal(str(self.paid_amount))
        return amount - paid
    
    @property
    def is_overdue(self):
        from datetime import date
        return self.due_date < date.today() and self.status != 'paid'
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            from datetime import date
            return (date.today() - self.due_date).days
        return 0
    
    def save(self, *args, **kwargs):
        if not self.bill_number:
            # Generate bill number
            last_bill = PatientBill.objects.order_by('-id').first()
            if last_bill:
                last_number = int(last_bill.bill_number.split('-')[1])
                self.bill_number = f'BILL-{last_number + 1:06d}'
            else:
                self.bill_number = 'BILL-000001'
        
        # Ensure amounts are Decimal for proper comparison
        from decimal import Decimal
        
        # Convert to Decimal if needed
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))
        if not isinstance(self.paid_amount, Decimal):
            self.paid_amount = Decimal(str(self.paid_amount))
        
        # Update status based on payment
        if self.paid_amount >= self.amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partially_paid'
        else:
            self.status = 'unpaid'
            
        super().save(*args, **kwargs)


class ExpenseCategory(models.Model):
    """Model for expense categories"""
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, default='blue')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('expense category')
        verbose_name_plural = _('expense categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DoctorPayment(models.Model):
    from doctors.models import Doctor
    
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE)
    payment_period = models.DateField()  # Month/period for which payment is made
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2)
    clinic_share = models.DecimalField(max_digits=10, decimal_places=2)  # 20%
    doctor_payout = models.DecimalField(max_digits=10, decimal_places=2)  # 80%
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, default='bank_transfer')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment to {self.doctor} for {self.payment_period.strftime('%B %Y')}"
    
    class Meta:
        unique_together = ['doctor', 'payment_period']
        verbose_name = "Doctor Payment"
        verbose_name_plural = "Doctor Payments"
        ordering = ['-payment_period']


class Expense(models.Model):
    """Model for tracking clinic expenses"""
    PAYMENT_METHODS = (
        ('cash', _('Cash')),
        ('credit_card', _('Credit Card')),
        ('bank_transfer', _('Bank Transfer')),
        ('check', _('Check')),
        ('other', _('Other')),
    )
    
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    expense_date = models.DateField()
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('expense')
        verbose_name_plural = _('expenses')
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.description} - ${self.amount}"
