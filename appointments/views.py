from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, time as datetime_time
from .models import Appointment
from .forms import AppointmentForm, AdminAppointmentForm
from doctors.models import Doctor, DoctorSchedule
from patients.models import Patient

@login_required
def appointment_list(request):
    """View for listing all appointments for the logged-in user.
    
    For doctors: Shows their own appointments
    For patients: Shows their own appointments
    For admins/staff: Shows all appointments
    """
    if hasattr(request.user, 'is_doctor') and request.user.is_doctor:
        # Doctor sees their own appointments
        appointments = Appointment.objects.filter(doctor=request.user.doctor)
    elif hasattr(request.user, 'patient'):
        # Patient sees their own appointments
        appointments = Appointment.objects.filter(patient=request.user.patient)
    else:
        # Admin/staff sees all appointments
        appointments = Appointment.objects.all()
    
    # Order by appointment date and time
    appointments = appointments.order_by('appointment_date', 'appointment_time')
    
    context = {
        'appointments': appointments,
        'is_admin': request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin',
        'is_patient': hasattr(request.user, 'patient')
    }
    return render(request, 'appointments/appointment_list.html', context)

@login_required
def book_appointment(request):
    """View for booking a new appointment. Only accessible by patients."""
    # Check if user is a patient
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'Only patients can book appointments.')
        return redirect('dashboard')  # or appropriate redirect
        
    if request.method == 'POST':
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient
            appointment.save()
            messages.success(request, 'Appointment booked successfully!')
            return redirect('appointments:list')
    else:
        form = AppointmentForm(user=request.user)
    
    return render(request, 'appointments/book_appointment.html', {'form': form})

@login_required
def appointment_detail(request, pk):
    """View for viewing appointment details."""
    appointment = get_object_or_404(Appointment, pk=pk)
    # Check if the user has permission to view this appointment
    if not (
        request.user == appointment.patient.user
        or request.user == appointment.doctor.user
        or request.user.is_staff
        or getattr(request.user, 'user_type', '') == 'admin'
    ):
        messages.error(request, 'You do not have permission to view this appointment.')
        return redirect('appointments:list')
    
    return render(request, 'appointments/appointment_detail.html', {'appointment': appointment})

@login_required
def cancel_appointment(request, pk):
    """View for canceling an appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)
    # Check if the user has permission to cancel this appointment
    if not (
        request.user == appointment.patient.user
        or request.user == appointment.doctor.user
        or request.user.is_staff
        or getattr(request.user, 'user_type', '') == 'admin'
    ):
        messages.error(request, "You don't have permission to cancel this appointment.")
        return redirect('appointments:list')
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        # Set cancellation timestamp and optional reason
        appointment.cancelled_at = timezone.now()
        reason = request.POST.get('cancellation_reason', '')
        if reason:
            appointment.cancellation_reason = reason
        appointment.save()
        messages.success(request, 'Appointment has been cancelled successfully.')
        return redirect('appointments:list')
    # For GET, redirect to the appointment detail; confirmation handled via UI popup
    return redirect('appointments:detail', pk=appointment.pk)

@login_required
def book_doctor_appointment(request, doctor_id):
    """View for booking an appointment with a specific doctor."""
    doctor = get_object_or_404(Doctor, id=doctor_id, is_available=True)
    
    # Ensure the user is a patient
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'Only patients can book appointments.')
        return redirect('home')
    
    patient = request.user.patient
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, doctor=doctor, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.doctor = doctor
            appointment.patient = patient
            appointment.status = 'scheduled'
            
            # Set the appointment time from the hidden fields
            appointment_date_str = request.POST.get('appointment_date')
            appointment_time_str = request.POST.get('appointment_time')
            
            if appointment_date_str and appointment_time_str:
                try:
                    appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
                    appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
                    
                    # Update the appointment date and time
                    appointment.appointment_date = appointment_date
                    appointment.appointment_time = appointment_time
                    
                    # Save the appointment
                    appointment.save()
                    
                    messages.success(request, 'Appointment booked successfully!')
                    return redirect('appointments:detail', pk=appointment.id)
                    
                except (ValueError, TypeError) as e:
                    messages.error(request, 'Invalid date or time format.')
            else:
                messages.error(request, 'Please select a valid date and time.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Initialize form with doctor and user
        form = AppointmentForm(doctor=doctor, user=request.user)
    
    # Get available time slots for the selected doctor
    available_slots = []
    today = timezone.now().date()
    
    # Get the next 7 days
    for day in range(7):
        current_date = today + timezone.timedelta(days=day)
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
        
        # Get the doctor's schedule for this day of the week
        schedule = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            is_working_day=True
        ).first()
        
        if schedule:
            # Generate time slots for this day
            current_time = datetime.combine(current_date, schedule.start_time)
            end_time = datetime.combine(current_date, schedule.end_time)
            slot_duration = timezone.timedelta(minutes=30)  # 30-minute slots
            
            while current_time + slot_duration <= end_time:
                # Check if the slot is available (not already booked)
                is_available = not Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=current_date,
                    appointment_time=current_time.time(),
                    status__in=['scheduled', 'confirmed']
                ).exists()
                
                slot = {
                    'date': current_date,
                    'time': current_time.time(),
                    'display_time': current_time.strftime('%I:%M %p'),
                    'is_available': is_available,
                    'date_iso': current_date.isoformat(),
                    'time_iso': current_time.time().strftime('%H:%M')
                }
                
                available_slots.append(slot)
                current_time += slot_duration
    
    # Group slots by date for the template
    slots_by_date = {}
    for slot in available_slots:
        date_str = slot['date'].strftime('%Y-%m-%d')
        if date_str not in slots_by_date:
            slots_by_date[date_str] = []
        slots_by_date[date_str].append(slot)
    
    context = {
        'form': form,
        'doctor': doctor,
        'slots_by_date': slots_by_date,
        'available_slots': available_slots,
        'today': today,
    }
    
    return render(request, 'appointments/book_doctor_appointment.html', context)

@login_required
def create_appointment(request):
    """Admin/Staff view to create an appointment between a patient and a doctor."""
    # Authorization: only staff or explicit admin user_type
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        messages.error(request, 'You do not have permission to create appointments.')
        return redirect('appointments:list')

    if request.method == 'POST':
        form = AdminAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, f'Appointment created successfully for {appointment.patient.user.get_full_name()}.')
            return redirect('appointments:detail', pk=appointment.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminAppointmentForm()

    # Get all active patients for the searchable dropdown
    all_patients = Patient.objects.select_related('user').filter(is_active=True).order_by('user__first_name', 'user__last_name')

    context = {
        'form': form,
        'all_patients': all_patients,
    }
    return render(request, 'appointments/create_appointment.html', context)

@login_required
def edit_appointment(request, pk):
    """Admin/Staff view to edit an existing appointment."""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        messages.error(request, 'You do not have permission to edit appointments.')
        return redirect('appointments:list')

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        form = AdminAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save()
            
            # Handle consultation fee if appointment is completed
            if appointment.status == 'completed':
                consultation_fee = request.POST.get('consultation_fee')
                payment_method = request.POST.get('payment_method')
                payment_notes = request.POST.get('payment_notes', '')
                
                if consultation_fee and payment_method:
                    from patients.models import PatientPayment
                    PatientPayment.objects.create(
                        patient=appointment.patient,
                        payment_type='consultation',
                        amount=consultation_fee,
                        payment_method=payment_method,
                        notes=f"Consultation with {appointment.doctor.user.get_full_name()} on {appointment.appointment_date}. {payment_notes}".strip()
                    )
                    messages.success(request, 'Appointment updated and consultation fee recorded successfully!')
                else:
                    messages.success(request, 'Appointment updated successfully!')
            else:
                messages.success(request, 'Appointment updated successfully!')
                
            return redirect('appointments:detail', pk=appointment.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminAppointmentForm(instance=appointment)

    context = {
        'form': form,
        'appointment': appointment,
    }
    return render(request, 'appointments/edit_appointment.html', context)
