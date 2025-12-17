from django import forms
from django.forms import ModelForm, DateInput, TimeInput, ModelChoiceField
from django.utils import timezone
from .models import Surgery, SurgeryType, OperationTheater, SurgeryTeam, SurgeryConsumable
from patients.models import Patient
from doctors.models import Doctor
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class SurgeryForm(forms.ModelForm):
    class Meta:
        model = Surgery
        fields = [
            'patient', 'surgeon', 'surgery_type', 'operation_theater',
            'scheduled_date', 'start_time', 'end_time', 'status', 'notes'
        ]
        widgets = {
            'scheduled_date': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set the initial surgeon to the current user if they are a doctor
        if user and hasattr(user, 'doctor'):
            self.fields['surgeon'].initial = user.doctor
        
        # Make surgery_type optional
        self.fields['surgery_type'].required = False
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['notes']:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        print("Form clean method called")
        print("Cleaned data:", cleaned_data)
        
        scheduled_date = cleaned_data.get('scheduled_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        operation_theater = cleaned_data.get('operation_theater')
        surgery_id = self.instance.id if self.instance else None

        # Check if end time is after start time
        if start_time and end_time and end_time <= start_time:
            print("End time validation failed")
            self.add_error('end_time', 'End time must be after start time')

        # Check for theater availability
        if scheduled_date and start_time and end_time and operation_theater:
            print("Checking theater availability...")
            # Check for overlapping surgeries in the same theater
            overlapping_surgeries = Surgery.objects.filter(
                operation_theater=operation_theater,
                scheduled_date=scheduled_date,
                status__in=['scheduled', 'in_progress'],
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            
            if surgery_id:  # Exclude current surgery when updating
                overlapping_surgeries = overlapping_surgeries.exclude(id=surgery_id)
            
            if overlapping_surgeries.exists():
                print("Theater is already booked")
                self.add_error('operation_theater', 
                    'This operation theater is already booked during the selected time slot.')

        print("Form clean completed successfully")
        return cleaned_data

class SurgeryTeamForm(forms.ModelForm):
    class Meta:
        model = SurgeryTeam
        fields = ['doctor', 'role', 'is_primary', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        surgery = kwargs.pop('surgery', None)
        super().__init__(*args, **kwargs)
        
        # Filter doctors who are not already in the surgery team
        if surgery:
            existing_doctors = SurgeryTeam.objects.filter(surgery=surgery).values_list('doctor', flat=True)
            self.fields['doctor'].queryset = Doctor.objects.exclude(id__in=existing_doctors)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['is_primary', 'notes']:
                field.widget.attrs.update({'class': 'form-control'})

class SurgeryConsumableForm(forms.ModelForm):
    class Meta:
        model = SurgeryConsumable
        fields = ['name', 'quantity', 'unit', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name != 'notes':
                field.widget.attrs.update({'class': 'form-control'})

class SurgeryStatusForm(forms.ModelForm):
    class Meta:
        model = Surgery
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Add any additional notes about the status change...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget.attrs.update({'class': 'form-control'})
