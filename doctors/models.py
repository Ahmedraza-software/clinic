from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Specialization(models.Model):
    """Model representing doctor specializations"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('specialization')
        verbose_name_plural = _('specializations')

class Doctor(models.Model):
    """Model representing a doctor in the clinic"""
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    specialization = models.ManyToManyField(Specialization, related_name='doctors')
    license_number = models.CharField(max_length=50, unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    bio = models.TextField(blank=True, null=True)
    experience = models.PositiveIntegerField(help_text=_("Years of experience"), default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.email}"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def phone(self):
        return self.user.phone
    
    class Meta:
        verbose_name = _('doctor')
        verbose_name_plural = _('doctors')

class DoctorSchedule(models.Model):
    """Model representing a doctor's working schedule"""
    DAYS_OF_WEEK = (
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    )
    
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_working_day = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('doctor schedule')
        verbose_name_plural = _('doctor schedules')
        unique_together = ('doctor', 'day_of_week')
    
    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"
