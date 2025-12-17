from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from datetime import datetime, time

from .models import Appointment
from doctors.models import Doctor, DoctorSchedule
from patients.models import Patient

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['appointment_type', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'appointment_date': forms.HiddenInput(),
            'appointment_time': forms.HiddenInput(),
            'appointment_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea mt-1 block w-full'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        
        # Set default appointment type if not provided
        if 'appointment_type' in self.fields and not self.instance.pk:
            self.fields['appointment_type'].initial = 'consultation'
            
        # Make reason field optional
        self.fields['reason'].required = False
        self.fields['appointment_date'].widget.attrs['min'] = timezone.now().date().isoformat()
        
        # Set time range (e.g., 9 AM to 5 PM)
        if 'appointment_time' in self.fields:
            self.fields['appointment_time'].widget.attrs['min'] = '09:00'
            self.fields['appointment_time'].widget.attrs['max'] = '17:00'
    
    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date < timezone.now().date():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return appointment_date
    
    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        
        if not all([appointment_date, appointment_time]):
            raise ValidationError(_('Please select both date and time for the appointment.'))
            
        # Combine date and time
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        if appointment_date and appointment_time:
            appointment_datetime = timezone.datetime.combine(appointment_date, appointment_time)
            if appointment_datetime < timezone.now():
                raise forms.ValidationError("Appointment date and time cannot be in the past.")
        
        return cleaned_data

class AdminAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'patient',
            'doctor',
            'appointment_type',
            'appointment_date',
            'appointment_time',
            'status',
            'notes',
        ]
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'appointment_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea mt-1 block w-full'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: limit choices to active users
        self.fields['patient'].queryset = Patient.objects.select_related('user').order_by('user__first_name', 'user__last_name')
        self.fields['doctor'].queryset = Doctor.objects.select_related('user').order_by('user__first_name', 'user__last_name')
        self.fields['notes'].required = False
        # Prevent past-date selection
        self.fields['appointment_date'].widget.attrs['min'] = timezone.now().date().isoformat()

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')

        if not all([doctor, appointment_date, appointment_time]):
            return cleaned_data

        # Prevent booking in the past
        dt = timezone.make_aware(datetime.combine(appointment_date, appointment_time))
        if dt < timezone.now():
            raise ValidationError(_('Appointment date and time cannot be in the past.'))

        # Prevent double booking for the doctor at the same time
        conflict_qs = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        )
        if self.instance.pk:
            conflict_qs = conflict_qs.exclude(pk=self.instance.pk)
        if conflict_qs.exists():
            raise ValidationError(_('This doctor already has an appointment at the selected time.'))

        return cleaned_data
