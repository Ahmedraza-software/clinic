from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.db import transaction
from datetime import date, timedelta

from appointments.models import Appointment
from patients.models import Patient
from .models import Doctor, DoctorSchedule, Specialization
from .forms import DoctorProfileForm, DoctorScheduleForm, DoctorSearchForm, CustomUserCreationForm, DoctorUserForm

# Custom decorator to check if user is a doctor
def doctor_required(view_func):
    decorated_view = user_passes_test(
        lambda u: hasattr(u, 'doctor'),
        login_url='home',
        redirect_field_name=None
    )(view_func)
    return decorated_view

# Custom decorator to check if user is admin
def admin_required(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(admin_required, login_url='home')
def add_doctor(request):
    """View for adding a new doctor (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to add doctors.')
        return redirect('home')
    
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        doctor_form = DoctorProfileForm(request.POST)
        
        if user_form.is_valid() and doctor_form.is_valid():
            try:
                with transaction.atomic():
                    # Save the user
                    user = user_form.save(commit=False)
                    user.is_active = True
                    user.user_type = 'doctor'
                    user.save()
                    
                    # Save the doctor profile
                    doctor = doctor_form.save(commit=False)
                    doctor.user = user
                    doctor.save()
                    # Save many-to-many relationships
                    doctor_form.save_m2m()
                    
                    messages.success(request, f'Doctor {user.get_full_name()} has been added successfully!')
                    return redirect('doctors:detail', pk=doctor.id)
                    
            except Exception as e:
                messages.error(request, f'An error occurred while saving the doctor: {str(e)}')
        else:
            # Combine form errors
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = CustomUserCreationForm()
        doctor_form = DoctorProfileForm()
    
    context = {
        'user_form': user_form,
        'doctor_form': doctor_form,
    }
    
    return render(request, 'doctors/add_doctor.html', context)

@login_required
@user_passes_test(admin_required, login_url='home')
def doctor_detail(request, pk):
    """View for admin to see doctor details"""
    doctor = get_object_or_404(Doctor, pk=pk)
    
    # Get upcoming appointments for this doctor (from today onwards)
    today = timezone.now().date()
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gte=today
    ).order_by('appointment_date', 'appointment_time')[:10]
    
    context = {
        'doctor': doctor,
        'upcoming_appointments': upcoming_appointments,
    }
    return render(request, 'doctors/doctor_detail.html', context)

@login_required
@user_passes_test(admin_required, login_url='home')
def doctor_edit(request, pk):
    """Admin view to edit a doctor's user info and profile"""
    doctor = get_object_or_404(Doctor, pk=pk)
    user = doctor.user
    if request.method == 'POST':
        user_form = DoctorUserForm(request.POST, instance=user)
        doctor_form = DoctorProfileForm(request.POST, instance=doctor)
        if user_form.is_valid() and doctor_form.is_valid():
            with transaction.atomic():
                user_form.save()
                doctor = doctor_form.save()
            messages.success(request, 'Doctor profile updated successfully.')
            return redirect('doctors:detail', pk=doctor.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = DoctorUserForm(instance=user)
        doctor_form = DoctorProfileForm(instance=doctor)
    context = {
        'user_form': user_form,
        'doctor_form': doctor_form,
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_edit.html', context)

def doctor_list(request):
    """
    View to display a list of all doctors with their specializations and availability.
    Patients can search and filter doctors by specialization, name, and availability.
    """
    doctors = Doctor.objects.filter(is_available=True).select_related('user').prefetch_related('specialization')
    specializations = Specialization.objects.annotate(doctor_count=Count('doctors')).filter(doctor_count__gt=0)
    
    # Initialize search form
    search_form = DoctorSearchForm(request.GET or None)
    
    # Apply filters if form is valid
    if search_form.is_valid():
        specialization = search_form.cleaned_data.get('specialization')
        name = search_form.cleaned_data.get('name')
        
        if specialization:
            doctors = doctors.filter(specialization=specialization)
        
        if name:
            doctors = doctors.filter(
                Q(user__first_name__icontains=name) | 
                Q(user__last_name__icontains=name) |
                Q(user__username__icontains=name)
            )
    
    # Get today's day of the week (0=Monday, 6=Sunday)
    today = timezone.now().date()
    today_weekday = today.weekday()  # 0=Monday, 6=Sunday
    
    # Get current time in the format 'HH:MM:SS'
    current_time = timezone.now().time()
    
    # Get available time slots for each doctor
    for doctor in doctors:
        # Get today's schedule for the doctor
        today_schedule = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=today_weekday,
            is_working_day=True
        ).first()
        
        doctor.today_schedule = today_schedule
        doctor.is_available_now = False
        
        if today_schedule:
            # Check if current time is within working hours
            if today_schedule.start_time <= current_time <= today_schedule.end_time:
                doctor.is_available_now = True
    
    context = {
        'doctors': doctors,
        'specializations': specializations,
        'search_form': search_form,
        'today': today,
    }
    
    return render(request, 'doctors/doctor_list.html', context)

@login_required
@doctor_required
def dashboard(request):
    """Doctor's dashboard view"""
    doctor = request.user.doctor
    today = timezone.now().date()
    
    # Get today's appointments
    appointments_today = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_time')
    
    # Get upcoming appointments (next 7 days)
    upcoming_date = today + timedelta(days=7)
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__range=[today, upcoming_date],
        status__in=['scheduled', 'confirmed']
    ).exclude(appointment_date=today).order_by('appointment_date', 'appointment_time')
    
    # Get recent appointments (last 5)
    recent_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__lt=today
    ).order_by('-appointment_date', '-appointment_time')[:5]
    
    context = {
        'appointments_today': appointments_today,
        'upcoming_appointments': upcoming_appointments,
        'recent_appointments': recent_appointments,
        'doctor': doctor,
    }
    
    return render(request, 'doctors/dashboard.html', context)

@login_required
@doctor_required
def appointment_list(request):
    """List all appointments for the doctor"""
    doctor = request.user.doctor
    
    # Get filter parameters
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Start with base queryset
    appointments = Appointment.objects.filter(doctor=doctor)
    
    # Apply filters
    if status:
        appointments = appointments.filter(status=status)
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    # Order by date and time
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    context = {
        'appointments': appointments,
        'status_filter': status,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'doctors/appointment_list.html', context)

@login_required
@doctor_required
def appointment_detail(request, pk):
    """View details of a specific appointment"""
    appointment = get_object_or_404(Appointment, pk=pk, doctor=request.user.doctor)
    
    if request.method == 'POST':
        # Handle status updates
        new_status = request.POST.get('status')
        if new_status in dict(Appointment.STATUS_CHOICES).keys():
            appointment.status = new_status
            appointment.save()
            messages.success(request, f'Appointment status updated to {appointment.get_status_display()}')
            return redirect('doctors:appointment_detail', pk=appointment.pk)
    
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'doctors/appointment_detail.html', context)

@login_required
@doctor_required
def profile(request):
    """Doctor's profile view"""
    doctor = request.user.doctor
    
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('doctors:profile')
    else:
        form = DoctorProfileForm(instance=doctor)
    
    context = {
        'form': form,
        'doctor': doctor,
    }
    
    return render(request, 'doctors/profile.html', context)

@login_required
@doctor_required
def schedule(request):
    """Doctor's schedule management"""
    doctor = request.user.doctor
    
    # Get or create doctor's schedule
    schedule, created = DoctorSchedule.objects.get_or_create(doctor=doctor)
    
    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your schedule has been updated.')
            return redirect('doctors:schedule')
    else:
        form = DoctorScheduleForm(instance=schedule)
    
    # Get doctor's availability
    availabilities = Availability.objects.filter(doctor=doctor)
    
    context = {
        'form': form,
        'availabilities': availabilities,
    }
    
    return render(request, 'doctors/schedule.html', context)

@login_required
@doctor_required
def add_availability(request):
    """Add a new availability slot"""
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.doctor = request.user.doctor
            
            # Check for overlapping availability
            if Availability.objects.filter(
                doctor=request.user.doctor,
                day_of_week=availability.day_of_week,
                start_time__lt=availability.end_time,
                end_time__gt=availability.start_time
            ).exists():
                messages.error(request, 'This time slot overlaps with an existing availability.')
            else:
                availability.save()
                messages.success(request, 'Availability added successfully.')
                return redirect('doctors:schedule')
    else:
        form = AvailabilityForm()
    
    context = {
        'form': form,
        'title': 'Add Availability',
    }
    
    return render(request, 'doctors/availability_form.html', context)

@login_required
@doctor_required
def edit_availability(request, pk):
    """Edit an existing availability slot"""
    availability = get_object_or_404(Availability, pk=pk, doctor=request.user.doctor)
    
    if request.method == 'POST':
        form = AvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            availability = form.save(commit=False)
            
            # Check for overlapping availability (excluding current one)
            if Availability.objects.filter(
                doctor=request.user.doctor,
                day_of_week=availability.day_of_week,
                start_time__lt=availability.end_time,
                end_time__gt=availability.start_time
            ).exclude(pk=availability.pk).exists():
                messages.error(request, 'This time slot overlaps with an existing availability.')
            else:
                availability.save()
                messages.success(request, 'Availability updated successfully.')
                return redirect('doctors:schedule')
    else:
        form = AvailabilityForm(instance=availability)
    
    context = {
        'form': form,
        'title': 'Edit Availability',
        'availability': availability,
    }
    
    return render(request, 'doctors/availability_form.html', context)

@login_required
@doctor_required
def delete_availability(request, pk):
    """Delete an availability slot"""
    availability = get_object_or_404(Availability, pk=pk, doctor=request.user.doctor)
    
    if request.method == 'POST':
        availability.delete()
        messages.success(request, 'Availability slot deleted successfully.')
        return redirect('doctors:schedule')
    
    context = {
        'availability': availability,
    }
    
    return render(request, 'doctors/confirm_delete_availability.html', context)

@login_required
@doctor_required
def patient_list(request):
    """List of patients who have appointments with the doctor"""
    doctor = request.user.doctor
    
    # Get unique patients who have appointments with this doctor
    patients = set()
    for appointment in Appointment.objects.filter(doctor=doctor).select_related('patient'):
        patients.add(appointment.patient)
    
    # Convert set to list for template
    patients = list(patients)
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        patients = [p for p in patients if 
                   search_query.lower() in p.user.get_full_name().lower() or
                   search_query.lower() in p.user.email.lower() or
                   (p.phone_number and search_query in p.phone_number)]
    
    context = {
        'patients': patients,
        'search_query': search_query,
    }
    
    return render(request, 'doctors/patient_list.html', context)

@login_required
@doctor_required
def patient_detail(request, pk):
    """View patient details and medical history"""
    patient = get_object_or_404(
        Patient,
        pk=pk,
        appointments__doctor=request.user.doctor
    )
    
    # Get all appointments with this patient
    appointments = Appointment.objects.filter(
        doctor=request.user.doctor,
        patient=patient
    ).order_by('-appointment_date', '-appointment_time')
    
    # Get medical records if available
    medical_records = getattr(patient, 'medical_records', None)
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
    }
    
    return render(request, 'doctors/patient_detail.html', context)
