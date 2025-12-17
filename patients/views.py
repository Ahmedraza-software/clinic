from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db import transaction
import csv
import io
from datetime import datetime, date
from .models import Patient, PatientDocument, PatientPayment
from appointments.models import Appointment
from .forms import PatientProfileForm, CustomUserCreationForm, PatientUserForm

def admin_required(user):
    return user.is_authenticated and (user.is_staff or getattr(user, 'user_type', '') == 'admin')

@login_required
def dashboard(request):
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('home')
        
    context = {
        'patient': request.user.patient,
    }
    return render(request, 'patients/dashboard.html', context)

@login_required
def profile(request):
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('home')
    
    patient = request.user.patient
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('patients:profile')
    else:
        form = PatientProfileForm(instance=patient)
    
    context = {
        'form': form,
        'patient': patient,
    }
    return render(request, 'patients/profile.html', context)


@login_required
def appointment_list(request):
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('home')
    
    patient = request.user.patient
    today = timezone.now().date()
    
    # Get filter parameters
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Start with all appointments for the patient
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date', '-appointment_time')
    
    # Apply filters
    if status:
        appointments = appointments.filter(status=status)
    
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    # Get upcoming and past appointments
    upcoming_appointments = appointments.filter(
        Q(appointment_date__gt=today) | 
        (Q(appointment_date=today) & Q(appointment_time__gte=timezone.now().time()))
    )
    
    past_appointments = appointments.filter(
        Q(appointment_date__lt=today) | 
        (Q(appointment_date=today) & Q(appointment_time__lt=timezone.now().time()))
    )
    
    context = {
        'patient': patient,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'patients/appointment_list.html', context)


@login_required
def medical_history(request):
    """View for patient's medical history"""
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('home')
    
    patient = request.user.patient
    
    # Get all medical records for the patient
    medical_records = PatientDocument.objects.filter(patient=patient, document_type='report').order_by('-uploaded_at')
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
    }
    
    return render(request, 'patients/medical_history.html', context)


@login_required
def prescription_list(request):
    """View for patient's prescription list"""
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('home')
    
    patient = request.user.patient
    
    # Get all prescriptions for the patient
    prescriptions = PatientDocument.objects.filter(patient=patient, document_type='prescription').order_by('-uploaded_at')
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
    }
    
    return render(request, 'patients/prescription_list.html', context)

@login_required
@user_passes_test(admin_required, login_url='home')
def patient_detail(request, pk):
    """View for admin to see patient details"""
    patient = get_object_or_404(Patient, pk=pk)
    
    # Get recent appointments for this patient
    recent_appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date', '-appointment_time')[:5]
    
    # Calculate total payments
    from django.db.models import Sum
    total_payments = patient.payments.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'patient': patient,
        'recent_appointments': recent_appointments,
        'total_payments': total_payments,
    }
    return render(request, 'patients/patient_detail.html', context)

@login_required
@user_passes_test(admin_required, login_url='home')
def patient_edit(request, pk):
    """Admin view to edit a patient's user info and profile"""
    patient = get_object_or_404(Patient, pk=pk)
    user = patient.user
    if request.method == 'POST':
        user_form = PatientUserForm(request.POST, instance=user)
        profile_form = PatientProfileForm(request.POST, instance=patient)
        
        # Handle new payment if provided
        new_payment_amount = request.POST.get('new_payment_amount')
        new_payment_method = request.POST.get('new_payment_method')
        new_payment_type = request.POST.get('new_payment_type')
        new_payment_notes = request.POST.get('new_payment_notes', '')
        
        if user_form.is_valid() and profile_form.is_valid():
            from django.db import transaction
            with transaction.atomic():
                user_form.save()
                profile_form.save()
                
                # Add new payment if provided
                if new_payment_amount and new_payment_method and new_payment_type:
                    PatientPayment.objects.create(
                        patient=patient,
                        payment_type=new_payment_type,
                        amount=new_payment_amount,
                        payment_method=new_payment_method,
                        notes=new_payment_notes
                    )
                    messages.success(request, 'Patient details updated and payment recorded successfully.')
                else:
                    messages.success(request, 'Patient details updated successfully.')
                    
            return redirect('patients:detail', pk=patient.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = PatientUserForm(instance=user)
        profile_form = PatientProfileForm(instance=patient)
    
    # Calculate total payments for display
    from django.db.models import Sum
    total_payments = patient.payments.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'user_form': user_form,
        'patient_form': profile_form,
        'patient': patient,
        'total_payments': total_payments,
    }
    return render(request, 'patients/patient_edit.html', context)

@login_required
@user_passes_test(admin_required, login_url='home')
@login_required
def add_patient(request):
    """View for adding a new patient (admin only)"""
    if not request.user.is_staff and not hasattr(request.user, 'is_admin'):
        messages.error(request, 'You do not have permission to add patients.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        patient_form = PatientProfileForm(request.POST)
        
        if user_form.is_valid() and patient_form.is_valid():
            try:
                with transaction.atomic():
                    # Save the user
                    user = user_form.save(commit=False)
                    user.is_active = True
                    user.save()
                    
                    # Save the patient profile
                    patient = patient_form.save(commit=False)
                    patient.user = user
                    patient.save()
                    
                    # Handle payment information
                    registration_fee = request.POST.get('registration_fee')
                    payment_method = request.POST.get('payment_method')
                    payment_notes = request.POST.get('payment_notes', '')
                    
                    if registration_fee and payment_method:
                        PatientPayment.objects.create(
                            patient=patient,
                            payment_type='registration',
                            amount=registration_fee,
                            payment_method=payment_method,
                            notes=payment_notes
                        )
                    
                    messages.success(request, f'Patient {user.get_full_name()} has been added successfully with payment recorded!')
                    return redirect('patients:detail', pk=patient.id)
                    
            except Exception as e:
                messages.error(request, f'An error occurred while saving the patient: {str(e)}')
        else:
            # Combine form errors
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = CustomUserCreationForm()
        patient_form = PatientProfileForm()
    
    context = {
        'user_form': user_form,
        'patient_form': patient_form,
        'active_page': 'patients',
    }
    
    return render(request, 'patients/add_patient.html', context)

@login_required
@user_passes_test(admin_required, login_url='home')
def patient_list(request):
    """List all patients (admin only)"""
    if not request.user.is_staff and not hasattr(request.user, 'is_admin'):
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    
    # Get all active patients (same as EMR patient selection)
    patients = Patient.objects.select_related('user').filter(is_active=True).order_by('-created_at')
    
    if search_query:
        patients = patients.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Add pagination - 50 patients per page for faster loading
    page = request.GET.get('page', 1)
    paginator = Paginator(patients, 50)
    
    try:
        patients_page = paginator.page(page)
    except PageNotAnInteger:
        patients_page = paginator.page(1)
    except EmptyPage:
        patients_page = paginator.page(paginator.num_pages)
    
    context = {
        'patients': patients_page,
        'search_query': search_query,
        'active_page': 'patients',
        'is_admin': True,
        'page_obj': patients_page,
        'paginator': paginator,
    }
    
    return render(request, 'patients/patient_list.html', context)

@login_required
def discharge_patient(request, pk):
    """Discharge a patient and optionally process final payment."""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        messages.error(request, 'You do not have permission to discharge patients.')
        return redirect('patients:detail', pk=pk)
    
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        confirm_discharge = request.POST.get('confirm_discharge')
        if not confirm_discharge:
            messages.error(request, 'Please confirm the discharge by checking the confirmation box.')
            return redirect('patients:detail', pk=pk)
        
        # Process final payment if provided
        final_payment_amount = request.POST.get('final_payment_amount')
        final_payment_method = request.POST.get('final_payment_method')
        discharge_notes = request.POST.get('discharge_notes', '')
        
        with transaction.atomic():
            # Update patient status
            patient.status = 'discharged'
            patient.save()
            
            # Create final payment if provided
            if final_payment_amount and final_payment_method and float(final_payment_amount) > 0:
                PatientPayment.objects.create(
                    patient=patient,
                    payment_type='discharge',
                    amount=final_payment_amount,
                    payment_method=final_payment_method,
                    notes=f"Final discharge payment. {discharge_notes}".strip()
                )
                messages.success(request, f'Patient {patient.full_name} has been discharged and final payment of ${final_payment_amount} has been recorded.')
            else:
                messages.success(request, f'Patient {patient.full_name} has been discharged successfully.')
    
    return redirect('patients:detail', pk=pk)

@login_required
def reactivate_patient(request, pk):
    """Reactivate a discharged patient."""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        messages.error(request, 'You do not have permission to reactivate patients.')
        return redirect('patients:detail', pk=pk)
    
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        patient.status = 'active'
        patient.save()
        messages.success(request, f'Patient {patient.full_name} has been reactivated successfully.')
    
    return redirect('patients:detail', pk=pk)

@login_required
@user_passes_test(admin_required)
def import_patients_csv(request):
    """Import patients from CSV file using bulk operations for speed."""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'Please select a CSV file to import.')
            return render(request, 'patients/import_patients.html')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return render(request, 'patients/import_patients.html')
        
        try:
            # Read and decode the CSV file
            csv_data = csv_file.read().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_data))
            
            # Skip header if exists
            headers = next(csv_reader, None)
            if headers and headers[0].lower() == 'id':
                next(csv_reader)  # Skip header row
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            User = get_user_model()
            
            # Prepare bulk data
            users_to_create = []
            patients_to_create = []
            existing_emails = set(User.objects.values_list('email', flat=True))
            
            # Process all rows first
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
                if len(row) < 17:  # Minimum required columns
                    errors.append(f"Row {row_num}: Insufficient columns")
                    skipped_count += 1
                    continue
                
                try:
                    # Extract data from CSV row
                    acode = row[0].strip()
                    fname = row[1].strip()
                    lname = row[2].strip()
                    address = row[3].strip()
                    sex = row[4].strip().lower()
                    dob_str = row[5].strip()
                    mobile = row[6].strip()
                    emerg_contact = row[7].strip()
                    cnic = row[8].strip()
                    status = row[9].strip().lower()
                    remarks = row[10].strip()
                    gurd = row[11].strip()
                    father_name = row[12].strip()
                    hsb_name = row[13].strip()
                    marital_status = row[14].strip()
                    created_date_str = row[15].strip()
                    created_by = row[16].strip() if len(row) > 16 else '1'
                    
                    # Validate and convert data
                    if not fname or not lname:
                        errors.append(f"Row {row_num}: First name and last name are required")
                        skipped_count += 1
                        continue
                    
                    # Convert gender
                    gender_map = {'male': 'M', 'female': 'F', 'm': 'M', 'f': 'F'}
                    gender = gender_map.get(sex, 'O')
                    
                    # Convert date of birth
                    try:
                        if dob_str.isdigit():
                            # Handle age as number
                            age = int(dob_str)
                            birth_year = datetime.now().year - age
                            dob = date(birth_year, 1, 1)  # Default to Jan 1st
                        else:
                            # Try to parse as date
                            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    except:
                        errors.append(f"Row {row_num}: Invalid date of birth '{dob_str}'")
                        skipped_count += 1
                        continue
                    
                    # Convert status
                    status_map = {'active': 'active', 'inactive': 'inactive'}
                    patient_status = status_map.get(status, 'active')
                    
                    # Generate unique email
                    base_email = f"{fname.lower()}.{lname.lower()}@clinic.com"
                    email = base_email
                    counter = 1
                    while email in existing_emails:
                        email = f"{fname.lower()}.{lname.lower()}.{counter}@clinic.com"
                        counter += 1
                    existing_emails.add(email)
                    
                    # Prepare user data
                    user_data = {
                        'email': email,
                        'first_name': fname,
                        'last_name': lname,
                        'is_active': True,
                        # Password will be set separately
                    }
                    users_to_create.append(user_data)
                    
                    # Prepare patient data (will be linked to user after creation)
                    patient_data = {
                        'address': address or '',
                        'phone': mobile or '',
                        'emergency_contact_name': emerg_contact or '',
                        'emergency_contact_phone': emerg_contact or '',
                        'emergency_contact_relation': gurd or '',
                        'marital_status': marital_status or '',
                        'status': patient_status,
                        'is_active': True,
                        'date_of_birth': dob,
                        'gender': gender,
                        # User will be set after bulk creation
                    }
                    patients_to_create.append(patient_data)
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    skipped_count += 1
                    continue
            
            # Bulk create users and patients
            if users_to_create:
                with transaction.atomic():
                    # Bulk create users without passwords first
                    created_users = User.objects.bulk_create([
                        User(**user_data) 
                        for user_data in users_to_create
                    ], batch_size=500)  # Process in batches of 500
                    
                    # Set passwords for all created users
                    for user in created_users:
                        user.set_password('default123')
                    
                    # Bulk update passwords
                    User.objects.bulk_update(created_users, ['password'], batch_size=500)
                    
                    # Link patients to users and bulk create
                    patient_objects = []
                    for i, patient_data in enumerate(patients_to_create):
                        patient_data['user'] = created_users[i]
                        patient_objects.append(Patient(**patient_data))
                    
                    Patient.objects.bulk_create(patient_objects, batch_size=500)
            
            # Show results
            if imported_count > 0:
                messages.success(request, f'Successfully imported {imported_count} patients in bulk!')
            if skipped_count > 0:
                messages.warning(request, f'Skipped {skipped_count} rows due to errors.')
            if errors:
                messages.error(request, f'Errors encountered: {"; ".join(errors[:5])}')  # Show first 5 errors
            
            return redirect('patients:import_patients_csv')
            
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
            return render(request, 'patients/import_patients.html')
    
    return render(request, 'patients/import_patients.html')
