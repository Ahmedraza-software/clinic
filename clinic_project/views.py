from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
from patients.models import Patient
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.http import HttpResponse, JsonResponse

# Main Pages
def home(request):
    """Render the home page."""
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    try:
        return render(request, 'home.html')
    except Exception as e:
        # Fallback to a simple response if there's a template error
        from django.http import HttpResponse
        return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Healis Clinic</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-50">
            <div class="min-h-screen flex items-center justify-center">
                <div class="max-w-md w-full bg-white rounded-lg shadow-md p-6">
                    <h1 class="text-2xl font-bold text-gray-900 mb-4">Healis Clinic</h1>
                    <p class="text-gray-600 mb-4">Welcome to our medical clinic management system.</p>
                    <div class="space-y-2">
                        <a href="/accounts/login/" class="block w-full bg-blue-600 text-white text-center py-2 px-4 rounded hover:bg-blue-700">Login</a>
                        <a href="/accounts/register/" class="block w-full bg-gray-600 text-white text-center py-2 px-4 rounded hover:bg-gray-700">Register</a>
                    </div>
                    <div class="mt-4 text-sm text-red-600">
                        <p>Template Error: {str(e)}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)

def about(request):
    """Render the about page."""
    return render(request, 'about.html')

def services(request):
    """Render the services page."""
    return render(request, 'services.html')

def contact(request):
    """Render the contact page."""
    return render(request, 'contact.html')

@never_cache
@login_required
def dashboard(request):
    """Render the user dashboard based on user type."""
    # Create a response with cache control headers
    response = None
    
    if request.user.user_type == 'doctor':
        response = render(request, 'doctors/dashboard.html', {'active_page': 'dashboard'})
    elif request.user.user_type == 'patient':
        response = render(request, 'patients/dashboard.html', {'active_page': 'dashboard'})
    else:  # admin, staff, or other user types
        from django.contrib.auth import get_user_model
        from django.contrib.auth.forms import UserCreationForm
        from patients.forms import PatientProfileForm
        from doctors.models import Doctor
        from appointments.models import Appointment
        from patients.models import PatientPayment
        from datetime import date
        from django.db.models import Sum
        
        User = get_user_model()
        
        # Handle patient form submission
        user_form = None
        patient_form = None
        if request.method == 'POST' and 'add_patient' in request.POST:
            user_form = UserCreationForm(request.POST)
            patient_form = PatientProfileForm(request.POST, request.FILES)
            
            if user_form.is_valid() and patient_form.is_valid():
                # Save the user first
                user = user_form.save(commit=False)
                user.email = request.POST.get('email', '')
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.is_active = True
                user.save()
                
                # Save the patient profile
                patient = patient_form.save(commit=False)
                patient.user = user
                patient.save()
                
                messages.success(request, 'Patient added successfully!')
                return redirect('dashboard')
        else:
            user_form = UserCreationForm()
            patient_form = PatientProfileForm()
        
        # Get today's date for filtering
        today = timezone.now().date()
        
        # Get all patients with related user data (ordered by most recent first)
        patients = Patient.objects.select_related('user').filter(is_active=True).order_by('-user__date_joined')
        
        # Get all doctors with related user data (ordered by most recent first)
        doctors = Doctor.objects.select_related('user').prefetch_related('specialization').order_by('-created_at')
        
        # Calculate revenue
        from datetime import datetime
        from decimal import Decimal
        current_month = today.replace(day=1)
        
        # Calculate monthly revenue with proper handling
        monthly_revenue = Decimal('0')
        for payment in PatientPayment.objects.filter(payment_date__gte=current_month):
            monthly_revenue += payment.amount
        
        # Calculate total revenue with proper handling  
        total_revenue = Decimal('0')
        for payment in PatientPayment.objects.all():
            total_revenue += payment.amount
        
        # Get recent payments count (last 7 days)
        from datetime import timedelta
        week_ago = today - timedelta(days=7)
        recent_payments_count = PatientPayment.objects.filter(
            payment_date__gte=week_ago
        ).count()
        
        # Prepare stats with fresh database queries
        stats = {
            'patients_count': Patient.objects.filter(is_active=True).count(),
            'doctors_count': doctors.count(),
            'today_appointments': Appointment.objects.filter(
                appointment_date=today
            ).count(),
            'monthly_revenue': monthly_revenue,
            'total_revenue': total_revenue,
        }
        
        # Get recent patients with user data (up to 2 for dashboard preview)
        recent_patients = []
        for patient in patients[:2]:
            recent_patients.append({
                'id': patient.id,
                'first_name': patient.user.first_name,
                'last_name': patient.user.last_name,
                'email': patient.user.email,
                'is_active': patient.user.is_active,
                'last_visit': patient.last_visit if hasattr(patient, 'last_visit') else None,
                'date_joined': patient.user.date_joined
            })
        
        # Get recent doctors with user data (up to 5)
        recent_doctors = []
        for doctor in doctors[:5]:
            recent_doctors.append({
                'id': doctor.id,
                'first_name': doctor.user.first_name,
                'last_name': doctor.user.last_name,
                'email': doctor.user.email,
                'specializations': ', '.join([spec.name for spec in doctor.specialization.all()]),
                'license_number': doctor.license_number,
                'experience': doctor.experience,
                'is_available': doctor.is_available,
                'created_at': doctor.created_at
            })
        
        # Upcoming appointments (admin overview - limit to 2 for dashboard preview)
        upcoming_appointments = Appointment.objects.select_related('patient__user', 'doctor__user') \
            .filter(appointment_date__gte=today) \
            .order_by('appointment_date', 'appointment_time')[:2]

        # Handle form submission
        form_errors = None
        if request.method == 'POST' and 'add_patient' in request.POST:
            from django.contrib.auth.forms import UserCreationForm
            from patients.forms import PatientProfileForm
            
            user_form = UserCreationForm(request.POST)
            patient_form = PatientProfileForm(request.POST)
            
            if user_form.is_valid() and patient_form.is_valid():
                # Save the user
                user = user_form.save(commit=False)
                user.email = request.POST.get('email')
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.save()
                
                # Save the patient profile
                patient = patient_form.save(commit=False)
                patient.user = user
                patient.save()
                
                messages.success(request, 'Patient added successfully!')
                return redirect('dashboard')
            else:
                form_errors = {
                    'user_errors': user_form.errors,
                    'patient_errors': patient_form.errors
                }
        else:
            from django.contrib.auth.forms import UserCreationForm
            from patients.forms import PatientProfileForm
            user_form = UserCreationForm()
            patient_form = PatientProfileForm()
        
        context = {
            'active_page': 'dashboard',
            'recent_patients': recent_patients,
            'recent_doctors': recent_doctors,
            'stats': stats,
            'recent_payments_count': recent_payments_count,
            'now': timezone.now(),
            'user_form': user_form,
            'patient_form': patient_form,
            'form_errors': form_errors,
            'upcoming_appointments': upcoming_appointments,
        }
        
        response = render(request, 'dashboard/admin_dashboard.html', context)
    
    # Add headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # HTTP 1.1
    response['Pragma'] = 'no-cache'  # HTTP 1.0
    response['Expires'] = '0'  # Proxies
    response['X-Timestamp'] = str(timezone.now().timestamp())  # For debugging
    
    return response

# Operation Theater Views
@login_required
def ot_management(request):
    """Operation Theater Management Dashboard"""
    context = {
        'active_page': 'ot_management',
        'page_title': 'Operation Theater Management'
    }
    return render(request, 'ot_management/dashboard.html', context)

@login_required
def blood_transfer(request):
    """Blood Transfer Management"""
    from blood_bank.models import Donor, BloodTransfer
    from blood_bank.views import get_donor_statistics, get_blood_inventory, get_blood_flow_totals
    from patients.models import Patient
    from doctors.models import Doctor
    
    # Get recent donors (last 10)
    recent_donors = Donor.objects.all().order_by('-registered_at')[:10]
    
    # Get recent blood transfers (last 1 for main display)
    recent_transfers = BloodTransfer.objects.all().order_by('-created_at')[:1]
    
    # Get all blood transfers for the popup
    all_transfers = BloodTransfer.objects.all().order_by('-created_at')
    
    # Get all patients and doctors for transfer dropdown
    patients = Patient.objects.filter(is_active=True).select_related('user').order_by('user__first_name')
    doctors = Doctor.objects.filter(is_available=True).select_related('user').prefetch_related('specialization').order_by('user__first_name')
    
    # Get blood flow totals for the graph
    blood_flow_totals = get_blood_flow_totals()
    
    context = {
        'active_page': 'blood_transfer',
        'page_title': 'Blood Transfer Management',
        'statistics': get_donor_statistics(),
        'inventory': get_blood_inventory(),
        'donors': recent_donors,
        'transfers': recent_transfers,
        'all_transfers': all_transfers,
        'patients': patients,
        'doctors': doctors,
        'total_units_in': blood_flow_totals['total_units_in'],
        'total_units_out': blood_flow_totals['total_units_out'],
    }
    return render(request, 'blood_bank/transfer.html', context)

@login_required
def patient_medical_history(request, patient_id=None):
    """Patient Medical History - Redirect to EMR app"""
    from django.urls import reverse
    
    if patient_id:
        return redirect(reverse('emr:patient_medical_history', kwargs={'patient_id': patient_id}))
    else:
        # Check if user is admin/staff - redirect to patient selection
        if (request.user.is_staff or request.user.is_superuser or 
            getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
            return redirect(reverse('emr:patient_selection'))
        else:
            # Regular patients view their own history
            return redirect(reverse('emr:my_medical_history'))

# Billing & Finance Views
@login_required
def patient_bills(request):
    """Patient Billing Management"""
    from patients.models import PatientPayment, PatientBill
    from decimal import Decimal
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get all bills and payments with search filtering
    bills_queryset = PatientBill.objects.select_related('patient__user').order_by('-bill_date')
    payments_queryset = PatientPayment.objects.select_related('patient__user').order_by('-payment_date')
    
    # Apply search filter if query exists
    if search_query:
        bills_queryset = bills_queryset.filter(
            Q(bill_number__icontains=search_query) |
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(patient__user__email__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
        payments_queryset = payments_queryset.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(patient__user__email__icontains=search_query) |
            Q(payment_type__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Combine bills and payments into a unified list
    all_records = []
    
    # Add actual bills
    for bill in bills_queryset:
        record = {
            'id': f'bill_{bill.id}',
            'type': 'bill',
            'bill_number': bill.bill_number,
            'patient': bill.patient,
            'bill_date': bill.bill_date,
            'due_date': bill.due_date,
            'total_amount': bill.amount,
            'paid_amount': bill.paid_amount,
            'remaining_amount': bill.remaining_amount,
            'status': bill.status,
            'payment_type': bill.description,
            'payment_method': 'N/A',
            'notes': bill.notes,
            'is_overdue': bill.is_overdue,
            'days_overdue': bill.days_overdue,
            'original_object': bill
        }
        all_records.append(record)
    
    # Add payments as paid records
    for payment in payments_queryset:
        record = {
            'id': f'payment_{payment.id}',
            'type': 'payment',
            'bill_number': f'PAY-{payment.id:06d}',
            'patient': payment.patient,
            'bill_date': payment.payment_date,
            'due_date': payment.payment_date,
            'total_amount': payment.amount,
            'paid_amount': payment.amount,
            'remaining_amount': Decimal('0'),
            'status': 'paid',
            'payment_type': payment.get_payment_type_display(),
            'payment_method': payment.get_payment_method_display(),
            'notes': payment.notes,
            'is_overdue': False,
            'days_overdue': 0,
            'original_object': payment
        }
        all_records.append(record)
    
    # Sort all records by date (newest first)
    all_records.sort(key=lambda x: x['bill_date'], reverse=True)
    
    # Pagination
    paginator = Paginator(all_records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary statistics
    total_bills = bills_queryset.count()
    
    # Calculate total paid: only count non-bill payments + bill payments separately to avoid double counting
    non_bill_payments = sum(payment.amount for payment in payments_queryset if payment.payment_type != 'bill_payment')
    bill_payments = sum(bill.paid_amount for bill in bills_queryset)
    total_paid = non_bill_payments + bill_payments
    
    total_pending = sum(bill.remaining_amount for bill in bills_queryset if bill.status in ['unpaid', 'partially_paid'])
    total_overdue = sum(bill.remaining_amount for bill in bills_queryset if bill.is_overdue)
    
    summary = {
        'total_bills': total_bills + payments_queryset.count(),
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_overdue': total_overdue
    }
    
    context = {
        'active_page': 'patient_bills',
        'page_title': 'Patient Billing',
        'bills': page_obj,
        'page_obj': page_obj,
        'summary': summary,
        'search_query': search_query
    }
    return render(request, 'billing/patient_bills.html', context)

@login_required
def export_patient_bills(request):
    """Export all patient bills and payments to CSV"""
    import csv
    from django.http import HttpResponse
    from patients.models import PatientBill, PatientPayment
    from datetime import datetime
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="patient_billing_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write CSV header
    writer.writerow([
        'Record ID',
        'Type',
        'Patient Name',
        'Patient Phone',
        'Description',
        'Amount',
        'Payment Method',
        'Status',
        'Date',
        'Created Date'
    ])
    
    # Collect all records (bills and payments)
    all_records = []
    
    # Get all bills
    bills = PatientBill.objects.select_related('patient__user').all()
    for bill in bills:
        all_records.append({
            'id': bill.bill_number,
            'type': 'Bill',
            'patient_name': bill.patient.user.get_full_name() if bill.patient.user else 'N/A',
            'patient_phone': bill.patient.phone or 'N/A',
            'description': bill.description,
            'amount': bill.amount,
            'payment_method': 'N/A',
            'status': bill.get_status_display(),
            'date': bill.bill_date,
            'created_date': bill.created_at
        })
    
    # Get all payments
    payments = PatientPayment.objects.select_related('patient__user').all()
    for payment in payments:
        all_records.append({
            'id': f'PAY-{payment.id:06d}',
            'type': 'Payment',
            'patient_name': payment.patient.user.get_full_name() if payment.patient.user else 'N/A',
            'patient_phone': payment.patient.phone or 'N/A',
            'description': payment.notes or payment.get_payment_type_display(),
            'amount': payment.amount,
            'payment_method': payment.get_payment_method_display(),
            'status': 'Paid',
            'date': payment.payment_date,
            'created_date': payment.created_at
        })
    
    # Sort all records by date (newest first)
    all_records.sort(key=lambda x: x['created_date'], reverse=True)
    
    # Write all records
    for record in all_records:
        writer.writerow([
            record['id'],
            record['type'],
            record['patient_name'],
            record['patient_phone'],
            record['description'],
            f"{record['amount']:.2f}",
            record['payment_method'],
            record['status'],
            record['date'].strftime('%m/%d/%Y %H:%M') if record['date'] else 'N/A',
            record['created_date'].strftime('%m/%d/%Y %H:%M') if record['created_date'] else 'N/A'
        ])
    
    return response

@login_required
def consultation_fees(request):
    """Consultation Fees Management with Appointments"""
    from appointments.models import Appointment
    from doctors.models import Doctor
    from patients.models import Patient
    from datetime import date
    
    # Get today's appointments
    today = date.today()
    appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('patient__user', 'doctor__user').order_by('appointment_time')
    
    # Get all patients and doctors for the appointment form
    patients = Patient.objects.select_related('user').filter(user__is_active=True).order_by('user__first_name')
    doctors = Doctor.objects.select_related('user').filter(user__is_active=True).order_by('user__first_name')
    
    context = {
        'active_page': 'consultation_fees',
        'page_title': 'Consultation Fees',
        'appointments': appointments,
        'patients': patients,
        'doctors': doctors,
    }
    return render(request, 'billing/consultation_fees.html', context)

@login_required
def create_appointment_api(request):
    """API endpoint to create appointments"""
    if request.method == 'POST':
        try:
            from appointments.models import Appointment
            from doctors.models import Doctor
            from patients.models import Patient
            from datetime import datetime
            
            # Get form data
            patient_id = request.POST.get('patient')
            doctor_id = request.POST.get('doctor')
            appointment_date = request.POST.get('appointment_date')
            appointment_time = request.POST.get('appointment_time')
            appointment_type = request.POST.get('appointment_type', 'consultation')
            status = request.POST.get('status', 'scheduled')
            reason = request.POST.get('reason', '')
            
            # Validate required fields
            if not all([patient_id, doctor_id, appointment_date, appointment_time]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            # Get patient and doctor objects
            try:
                patient = Patient.objects.get(id=patient_id)
                doctor = Doctor.objects.get(id=doctor_id)
            except (Patient.DoesNotExist, Doctor.DoesNotExist):
                return JsonResponse({'success': False, 'error': 'Invalid patient or doctor'})
            
            # Parse date and time
            try:
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                appointment_time = datetime.strptime(appointment_time, '%H:%M').time()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date or time format'})
            
            # Check for conflicts (same doctor, date, time)
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['scheduled', 'confirmed']
            ).exists()
            
            if existing:
                return JsonResponse({'success': False, 'error': 'Doctor already has an appointment at this time'})
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                appointment_type=appointment_type,
                status=status,
                reason=reason,
                notes=reason  # Use reason as notes as well
            )
            
            return JsonResponse({
                'success': True,
                'appointment_id': appointment.id,
                'message': 'Appointment created successfully'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def accounts_finance(request):
    """Accounts and Finance Overview with Real Data"""
    from patients.models import PatientPayment, PatientBill, Expense, ExpenseCategory
    from decimal import Decimal
    from datetime import date, timedelta
    from django.db.models import Sum, Count, Q
    from calendar import month_name
    import json
    
    today = date.today()
    current_month = today.replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    last_month_end = current_month - timedelta(days=1)
    
    # Calculate Revenue (from PatientPayments)
    current_month_revenue = PatientPayment.objects.filter(
        payment_date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    last_month_revenue = PatientPayment.objects.filter(
        payment_date__gte=last_month,
        payment_date__lte=last_month_end
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate revenue change percentage
    if last_month_revenue > 0:
        revenue_change = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100)
    else:
        revenue_change = 100 if current_month_revenue > 0 else 0
    
    # Calculate Expenses
    current_month_expenses = Expense.objects.filter(
        expense_date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    last_month_expenses = Expense.objects.filter(
        expense_date__gte=last_month,
        expense_date__lte=last_month_end
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate expense change percentage
    if last_month_expenses > 0:
        expense_change = ((current_month_expenses - last_month_expenses) / last_month_expenses * 100)
    else:
        expense_change = 100 if current_month_expenses > 0 else 0
    
    # Calculate Net Profit
    net_profit = current_month_revenue - current_month_expenses
    last_month_net_profit = last_month_revenue - last_month_expenses
    
    # Calculate net profit change percentage
    if last_month_net_profit != 0:
        net_profit_change = ((net_profit - last_month_net_profit) / abs(last_month_net_profit) * 100)
    else:
        net_profit_change = 100 if net_profit > 0 else -100 if net_profit < 0 else 0
    
    # Calculate Outstanding (unpaid and partially paid bills)
    from django.db.models import F
    outstanding_bills_data = PatientBill.objects.filter(
        status__in=['unpaid', 'partially_paid']
    ).aggregate(
        total_amount=Sum('amount'),
        total_paid=Sum('paid_amount')
    )
    
    total_amount = outstanding_bills_data['total_amount'] or Decimal('0')
    total_paid = outstanding_bills_data['total_paid'] or Decimal('0')
    outstanding_bills = total_amount - total_paid
    
    # Count overdue payments
    overdue_count = PatientBill.objects.filter(
        status__in=['unpaid', 'partially_paid'],
        due_date__lt=today
    ).count()
    
    # Revenue vs Expenses for last 6 months
    revenue_vs_expenses = []
    labels_6_months = []
    
    for i in range(5, -1, -1):
        month_start = (current_month - timedelta(days=32*i)).replace(day=1)
        month_end = (month_start.replace(month=month_start.month % 12 + 1) if month_start.month < 12 
                    else month_start.replace(year=month_start.year + 1, month=1)) - timedelta(days=1)
        
        month_revenue = PatientPayment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        month_expenses = Expense.objects.filter(
            expense_date__gte=month_start,
            expense_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        revenue_vs_expenses.append({
            'revenue': float(month_revenue),
            'expenses': float(month_expenses)
        })
        labels_6_months.append(month_name[month_start.month][:3])
    
    # Recent Transactions (mix of payments and expenses)
    recent_payments = PatientPayment.objects.select_related('patient__user').order_by('-payment_date')[:10]
    recent_expenses = Expense.objects.select_related('category').order_by('-expense_date')[:10]
    
    # Combine and sort recent transactions
    recent_transactions = []
    
    for payment in recent_payments:
        recent_transactions.append({
            'date': payment.payment_date.date() if hasattr(payment.payment_date, 'date') else payment.payment_date,
            'description': f"Payment from {payment.patient.user.get_full_name() if payment.patient.user else 'Unknown'}",
            'category': payment.get_payment_type_display(),
            'amount': payment.amount,
            'type': 'revenue'
        })
    
    for expense in recent_expenses:
        recent_transactions.append({
            'date': expense.expense_date,
            'description': expense.description,
            'category': expense.category.name,
            'amount': -expense.amount,  # Negative for expenses
            'type': 'expense'
        })
    
    # Sort by date (newest first) and take top 10
    recent_transactions.sort(key=lambda x: x['date'], reverse=True)
    recent_transactions = recent_transactions[:10]
    
    # Doctor revenue analysis
    from appointments.models import Appointment
    from doctors.models import Doctor
    from patients.models import DoctorPayment
    
    doctor_revenues = []
    total_doctor_revenue = Decimal('0')
    
    # Get all active doctors
    doctors = Doctor.objects.select_related('user').filter(user__is_active=True)
    
    for doctor in doctors:
        # Get doctor payment record (this has the correct calculated revenue)
        doctor_payment = DoctorPayment.objects.filter(
            doctor=doctor,
            payment_period=current_month
        ).first()
        
        # Use the revenue from DoctorPayment record if it exists
        doctor_revenue = doctor_payment.revenue_generated if doctor_payment else Decimal('0')
        
        # Count completed appointments for this doctor this month
        completed_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__gte=current_month,
            status='completed'
        )
        appointment_count = completed_appointments.count()
        
        # Count consultation payments using the same improved logic
        doctor_name = doctor.user.get_full_name() if doctor.user else str(doctor)
        
        # Find payments that mention this doctor
        doctor_specific_payments = PatientPayment.objects.filter(
            payment_date__gte=current_month,
            notes__icontains=doctor_name
        )
        
        # Also find payments around appointment dates
        appointment_payments = []
        for appointment in completed_appointments:
            payments = PatientPayment.objects.filter(
                patient=appointment.patient,
                payment_date__gte=appointment.appointment_date - timedelta(days=7),
                payment_date__lte=appointment.appointment_date + timedelta(days=7),
                payment_type__in=['consultation_fee', 'appointment_fee']
            )
            appointment_payments.extend(payments)
        
        # Combine and count unique payments
        all_payments = list(doctor_specific_payments) + appointment_payments
        unique_payments = list({payment.id: payment for payment in all_payments}.values())
        consultation_count = len(unique_payments)
        
        total_doctor_revenue += doctor_revenue
        
        # Get doctor initials
        name_parts = doctor_name.split()
        initials = ''.join([part[0].upper() for part in name_parts if part]) if name_parts else 'UN'
        
        # Only include doctors with revenue or appointments
        if doctor_revenue > 0 or appointment_count > 0:
            doctor_revenues.append({
                'doctor_id': doctor.id,
                'doctor_name': doctor_name,
                'doctor_email': doctor.user.email if doctor.user else '',
                'doctor_initials': initials,
                'specialty': doctor.specialty if hasattr(doctor, 'specialty') else 'General',
                'appointment_count': appointment_count,
                'consultation_count': consultation_count,
                'total_revenue': doctor_revenue
            })
    
    # Sort by revenue (highest first)
    doctor_revenues.sort(key=lambda x: x['total_revenue'], reverse=True)
    
    # Calculate total completed appointments for summary
    total_completed_appointments = sum(dr['appointment_count'] for dr in doctor_revenues)
    
    # Calculate doctor payouts (80% to doctors, 20% to clinic)
    clinic_share_percentage = Decimal('0.20')  # 20%
    doctor_share_percentage = Decimal('0.80')  # 80%
    
    clinic_share = total_doctor_revenue * clinic_share_percentage
    total_doctor_payouts = total_doctor_revenue * doctor_share_percentage
    
    # Create doctor payout data using DoctorPayment model
    from patients.models import DoctorPayment
    from django.utils import timezone
    
    doctor_payouts = []
    for doctor_data in doctor_revenues:
        if doctor_data['total_revenue'] > 0:
            doctor_clinic_share = doctor_data['total_revenue'] * clinic_share_percentage
            doctor_payout = doctor_data['total_revenue'] * doctor_share_percentage
            
            # Get or create DoctorPayment record for this month
            doctor_payment, created = DoctorPayment.objects.get_or_create(
                doctor_id=doctor_data['doctor_id'],
                payment_period=current_month,
                defaults={
                    'revenue_generated': doctor_data['total_revenue'],
                    'clinic_share': doctor_clinic_share,
                    'doctor_payout': doctor_payout,
                    'created_by': request.user
                }
            )
            
            # Update amounts if record exists but amounts changed
            if not created:
                doctor_payment.revenue_generated = doctor_data['total_revenue']
                doctor_payment.clinic_share = doctor_clinic_share
                doctor_payment.doctor_payout = doctor_payout
                doctor_payment.save()
            
            doctor_payouts.append({
                'doctor_id': doctor_data['doctor_id'],
                'doctor_name': doctor_data['doctor_name'],
                'doctor_initials': doctor_data['doctor_initials'],
                'specialty': doctor_data['specialty'],
                'total_revenue': doctor_data['total_revenue'],
                'clinic_share': doctor_clinic_share,
                'doctor_payout': doctor_payout,
                'is_paid': doctor_payment.is_paid,
                'payment_date': doctor_payment.payment_date
            })
    
    # Prepare chart data
    chart_data = {
        'revenue_vs_expenses': {
            'labels': labels_6_months,
            'revenue_data': [item['revenue'] for item in revenue_vs_expenses],
            'expense_data': [item['expenses'] for item in revenue_vs_expenses]
        }
    }
    
    context = {
        'active_page': 'accounts_finance',
        'page_title': 'Accounts & Finance',
        'current_month_revenue': current_month_revenue,
        'revenue_change': round(revenue_change, 1),
        'current_month_expenses': current_month_expenses,
        'expense_change': round(expense_change, 1),
        'net_profit': net_profit,
        'net_profit_change': round(net_profit_change, 1),
        'outstanding_bills': outstanding_bills,
        'overdue_count': overdue_count,
        'doctor_revenues': doctor_revenues,
        'total_doctor_revenue': total_doctor_revenue,
        'total_completed_appointments': total_completed_appointments,
        'clinic_share': clinic_share,
        'total_doctor_payouts': total_doctor_payouts,
        'doctor_payouts': doctor_payouts,
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'finance/accounts.html', context)

@login_required
def expenses(request):
    """Expense Tracking"""
    from patients.models import Expense, ExpenseCategory
    from decimal import Decimal
    from datetime import date, timedelta
    from django.db.models import Sum, Count
    
    # Handle expense creation and editing
    if request.method == 'POST':
        try:
            expense_id = request.POST.get('expense_id')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            category_name = request.POST.get('category')
            payment_method = request.POST.get('payment_method')
            expense_date = request.POST.get('date')
            notes = request.POST.get('notes', '')
            is_recurring = request.POST.get('recurring') == 'on'
            
            # Validate required fields
            if not all([description, amount, category_name, payment_method, expense_date]):
                messages.error(request, 'All required fields must be filled.')
                return redirect('expenses')
            
            # Get or create category
            category, created = ExpenseCategory.objects.get_or_create(
                name=category_name,
                defaults={'color': 'blue'}
            )
            
            if expense_id:
                # Update existing expense
                expense = Expense.objects.get(id=expense_id)
                expense.description = description
                expense.amount = Decimal(amount)
                expense.category = category
                expense.payment_method = payment_method.lower().replace(' ', '_')
                expense.expense_date = expense_date
                expense.notes = notes
                expense.is_recurring = is_recurring
                expense.save()
                messages.success(request, 'Expense updated successfully!')
            else:
                # Create new expense
                expense = Expense.objects.create(
                    description=description,
                    amount=Decimal(amount),
                    category=category,
                    payment_method=payment_method.lower().replace(' ', '_'),
                    expense_date=expense_date,
                    notes=notes,
                    is_recurring=is_recurring,
                    created_by=request.user
                )
                messages.success(request, 'Expense added successfully!')
            
            return redirect('expenses')
            
        except Exception as e:
            messages.error(request, f'Error processing expense: {str(e)}')
            return redirect('expenses')
    
    # Get expense data
    expenses = Expense.objects.select_related('category', 'created_by').order_by('-expense_date')[:20]
    
    # Calculate summary statistics
    today = date.today()
    current_month = today.replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    # Total expenses this month
    total_expenses = Expense.objects.filter(
        expense_date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Last month expenses for comparison
    last_month_expenses = Expense.objects.filter(
        expense_date__gte=last_month,
        expense_date__lt=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate percentage change
    if last_month_expenses > 0:
        expense_change = ((total_expenses - last_month_expenses) / last_month_expenses * 100)
    else:
        expense_change = 0 if total_expenses == 0 else 100
    
    # Categories count
    categories_count = ExpenseCategory.objects.filter(is_active=True).count()
    
    # Recurring expenses
    recurring_expenses = Expense.objects.filter(
        is_recurring=True
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Average daily spend
    days_in_month = today.day
    avg_daily_spend = total_expenses / days_in_month if days_in_month > 0 else Decimal('0')
    
    # Get categories for form
    expense_categories = ExpenseCategory.objects.filter(is_active=True).order_by('name')
    
    # Prepare chart data
    from django.db.models import Q
    import json
    from calendar import month_name
    
    # Expenses over time (last 12 months)
    expenses_over_time = []
    labels_over_time = []
    
    for i in range(11, -1, -1):
        month_start = (current_month - timedelta(days=32*i)).replace(day=1)
        month_end = (month_start.replace(month=month_start.month % 12 + 1) if month_start.month < 12 
                    else month_start.replace(year=month_start.year + 1, month=1)) - timedelta(days=1)
        
        month_total = Expense.objects.filter(
            expense_date__gte=month_start,
            expense_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses_over_time.append(float(month_total))
        labels_over_time.append(month_name[month_start.month][:3])
    
    # Expenses by category (current month)
    category_expenses = Expense.objects.filter(
        expense_date__gte=current_month
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    category_labels = []
    category_data = []
    category_colors = [
        'rgba(79, 70, 229, 0.8)',
        'rgba(99, 102, 241, 0.8)', 
        'rgba(129, 140, 248, 0.8)',
        'rgba(165, 180, 252, 0.8)',
        'rgba(199, 210, 254, 0.8)',
        'rgba(224, 231, 255, 0.8)',
        'rgba(244, 63, 94, 0.8)',
        'rgba(34, 197, 94, 0.8)',
        'rgba(234, 179, 8, 0.8)',
        'rgba(168, 85, 247, 0.8)'
    ]
    
    for i, category in enumerate(category_expenses):
        category_labels.append(category['category__name'])
        category_data.append(float(category['total']))
    
    # Serialize chart data as JSON
    chart_data_json = json.dumps({
        'expenses_over_time': {
            'labels': labels_over_time,
            'data': expenses_over_time
        },
        'expenses_by_category': {
            'labels': category_labels,
            'data': category_data,
            'colors': category_colors[:len(category_labels)]
        }
    })
    
    context = {
        'active_page': 'expenses',
        'page_title': 'Expense Tracking',
        'recent_expenses': expenses,
        'total_expenses': total_expenses,
        'expense_change': round(expense_change, 1),
        'categories_count': categories_count,
        'recurring_expenses': recurring_expenses,
        'avg_daily_spend': avg_daily_spend,
        'expense_categories': expense_categories,
        'chart_data': chart_data_json,
    }
    return render(request, 'finance/expenses.html', context)

@login_required
def get_expense(request, expense_id):
    """Get expense data for editing"""
    try:
        from patients.models import Expense
        expense = Expense.objects.get(id=expense_id)
        
        data = {
            'id': expense.id,
            'description': expense.description,
            'amount': str(expense.amount),
            'category': expense.category.name,
            'payment_method': expense.payment_method,
            'expense_date': expense.expense_date.strftime('%Y-%m-%d'),
            'notes': expense.notes or '',
            'is_recurring': expense.is_recurring
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def delete_expense(request, expense_id):
    """Delete an expense"""
    if request.method == 'POST':
        try:
            from patients.models import Expense
            expense = Expense.objects.get(id=expense_id)
            expense.delete()
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def pay_doctor(request):
    """Process doctor payment"""
    if request.method == 'POST':
        try:
            import json
            from django.utils import timezone
            from datetime import date
            data = json.loads(request.body)
            doctor_id = data.get('doctor_id')
            amount = data.get('amount')
            
            if not doctor_id or not amount:
                return JsonResponse({'success': False, 'error': 'Missing doctor ID or amount'})
            
            from doctors.models import Doctor
            from patients.models import DoctorPayment, Expense, ExpenseCategory
            from decimal import Decimal
            
            # Get the doctor
            doctor = Doctor.objects.get(id=doctor_id)
            
            # Get current month
            today = date.today()
            current_month = today.replace(day=1)
            
            # Get the DoctorPayment record
            doctor_payment = DoctorPayment.objects.get(
                doctor_id=doctor_id,
                payment_period=current_month
            )
            
            # Check if already paid
            if doctor_payment.is_paid:
                return JsonResponse({'success': False, 'error': 'Doctor has already been paid for this period'})
            
            # Mark as paid
            doctor_payment.is_paid = True
            doctor_payment.payment_date = timezone.now()
            doctor_payment.notes = f'Payment processed by {request.user.get_full_name()}'
            doctor_payment.save()
            
            # Create expense record for the payout (this reduces clinic's net profit)
            payout_category, created = ExpenseCategory.objects.get_or_create(
                name='Doctor Payouts',
                defaults={'color': 'purple', 'description': 'Payments made to doctors'}
            )
            
            expense = Expense.objects.create(
                description=f'Payment to Dr. {doctor.user.get_full_name() if doctor.user else "Unknown"}',
                amount=Decimal(str(amount)),
                category=payout_category,
                payment_method='bank_transfer',
                expense_date=today,
                notes=f'Doctor payout for revenue share - 80% of ${doctor_payment.revenue_generated}',
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Payment of ${amount:.2f} processed successfully for Dr. {doctor.user.get_full_name() if doctor.user else "Unknown"}. Status updated to PAID.'
            })
            
        except Doctor.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Doctor not found'})
        except DoctorPayment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Doctor payment record not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def refresh_financial_data(request):
    """API endpoint to get updated financial data without page reload"""
    if request.method == 'GET':
        try:
            from patients.models import PatientPayment, PatientBill, Expense, ExpenseCategory, DoctorPayment
            from decimal import Decimal
            from datetime import date, timedelta
            from django.db.models import Sum, Count
            import json
            
            today = date.today()
            current_month = today.replace(day=1)
            
            # Calculate current month revenue
            current_month_revenue = PatientPayment.objects.filter(
                payment_date__gte=current_month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Calculate current month expenses
            current_month_expenses = Expense.objects.filter(
                expense_date__gte=current_month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Calculate net profit
            net_profit = current_month_revenue - current_month_expenses
            
            # Calculate total doctor revenue and get detailed doctor data
            total_doctor_revenue = Decimal('0')
            total_completed_appointments = 0
            doctor_revenues_data = []
            
            from appointments.models import Appointment
            from doctors.models import Doctor
            
            # Get all active doctors
            doctors = Doctor.objects.select_related('user').filter(user__is_active=True)
            
            for doctor in doctors:
                # Get doctor payment record (this has the correct calculated revenue)
                doctor_payment = DoctorPayment.objects.filter(
                    doctor=doctor,
                    payment_period=current_month
                ).first()
                
                # Use the revenue from DoctorPayment record if it exists
                doctor_revenue = doctor_payment.revenue_generated if doctor_payment else Decimal('0')
                
                # Count completed appointments for this doctor this month
                completed_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date__gte=current_month,
                    status='completed'
                )
                appointment_count = completed_appointments.count()
                
                # Count consultation payments using the same improved logic
                doctor_name = doctor.user.get_full_name() if doctor.user else str(doctor)
                
                # Find payments that mention this doctor
                doctor_specific_payments = PatientPayment.objects.filter(
                    payment_date__gte=current_month,
                    notes__icontains=doctor_name
                )
                
                # Also find payments around appointment dates
                appointment_payments = []
                for appointment in completed_appointments:
                    payments = PatientPayment.objects.filter(
                        patient=appointment.patient,
                        payment_date__gte=appointment.appointment_date - timedelta(days=7),
                        payment_date__lte=appointment.appointment_date + timedelta(days=7),
                        payment_type__in=['consultation_fee', 'appointment_fee']
                    )
                    appointment_payments.extend(payments)
                
                # Combine and count unique payments
                all_payments = list(doctor_specific_payments) + appointment_payments
                unique_payments = list({payment.id: payment for payment in all_payments}.values())
                consultation_count = len(unique_payments)
                
                # Only include doctors with revenue or appointments
                if doctor_revenue > 0 or appointment_count > 0:
                    # Get doctor initials
                    name_parts = doctor_name.split()
                    initials = ''.join([part[0].upper() for part in name_parts if part]) if name_parts else 'UN'
                    
                    doctor_revenues_data.append({
                        'doctor_id': doctor.id,
                        'doctor_name': doctor_name,
                        'doctor_email': doctor.user.email if doctor.user else '',
                        'doctor_initials': initials,
                        'specialty': doctor.specialty if hasattr(doctor, 'specialty') else 'General',
                        'appointment_count': appointment_count,
                        'consultation_count': consultation_count,
                        'total_revenue': float(doctor_revenue)
                    })
                
                total_doctor_revenue += doctor_revenue
                total_completed_appointments += appointment_count
            
            # Sort by revenue (highest first)
            doctor_revenues_data.sort(key=lambda x: x['total_revenue'], reverse=True)
            
            # Calculate clinic share and doctor payouts
            clinic_share = total_doctor_revenue * Decimal('0.20')
            total_doctor_payouts = total_doctor_revenue * Decimal('0.80')
            
            return JsonResponse({
                'success': True,
                'data': {
                    'current_month_revenue': float(current_month_revenue),
                    'current_month_expenses': float(current_month_expenses),
                    'net_profit': float(net_profit),
                    'total_doctor_revenue': float(total_doctor_revenue),
                    'total_completed_appointments': total_completed_appointments,
                    'clinic_share': float(clinic_share),
                    'total_doctor_payouts': float(total_doctor_payouts),
                    'doctor_revenues': doctor_revenues_data
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def transactions(request):
    """Financial Transactions Overview"""
    # Add your transaction-related logic here
    context = {
        'active_page': 'transactions',
        'page_title': 'Financial Transactions'
    }
    return render(request, 'finance/transactions.html', context)

# Management Views
@login_required
def inventory_management(request):
    """Inventory Management"""
    context = {
        'active_page': 'inventory',
        'page_title': 'Inventory Management'
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
def patient_reviews(request):
    """Patient Reviews and Feedback"""
    context = {
        'active_page': 'reviews',
        'page_title': 'Patient Reviews'
    }
    return render(request, 'complaints_reviews/reviews.html', context)

@login_required
def complaints(request):
    """Patient Complaints Management"""
    context = {
        'active_page': 'complaints',
        'page_title': 'Patient Complaints'
    }
    return render(request, 'complaints_reviews/complaints.html', context)

@login_required
def revenue_details(request):
    """API endpoint to get monthly revenue details"""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    from patients.models import PatientPayment
    from decimal import Decimal
    from datetime import date
    
    # Get current month payments
    today = timezone.now().date()
    current_month = today.replace(day=1)
    
    monthly_payments = PatientPayment.objects.filter(
        payment_date__gte=current_month
    ).select_related('patient__user').order_by('-payment_date')
    
    # Calculate total
    total_revenue = Decimal('0')
    for payment in monthly_payments:
        total_revenue += payment.amount
    
    # Prepare payment data
    payments_data = []
    for payment in monthly_payments:
        payments_data.append({
            'id': payment.id,
            'patient_name': payment.patient.full_name,
            'amount': str(payment.amount),
            'payment_type': payment.payment_type,
            'payment_type_display': payment.get_payment_type_display(),
            'payment_method': payment.payment_method,
            'payment_method_display': payment.get_payment_method_display(),
            'payment_date': payment.payment_date.strftime('%b %d, %Y at %I:%M %p'),
            'notes': payment.notes or ''
        })
    
    return JsonResponse({
        'payments': payments_data,
        'total': str(total_revenue),
        'count': len(payments_data),
        'month': current_month.strftime('%B %Y')
    })

@login_required
def patient_payments(request, patient_id):
    """API endpoint to get all payments and bills for a specific patient"""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    from patients.models import PatientPayment, PatientBill, Patient
    from decimal import Decimal
    
    # Get the patient
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    
    # Get all payments for this patient
    patient_payments = PatientPayment.objects.filter(
        patient=patient
    ).order_by('-payment_date')
    
    # Get all bills for this patient
    patient_bills = PatientBill.objects.filter(
        patient=patient
    ).order_by('-bill_date')
    
    # Calculate totals
    total_paid = Decimal('0')
    total_due = Decimal('0')
    
    # Only count non-bill payments to avoid double counting
    for payment in patient_payments:
        if payment.payment_type != 'bill_payment':
            total_paid += payment.amount
    
    for bill in patient_bills:
        total_paid += bill.paid_amount
        total_due += bill.remaining_amount
    
    # Prepare combined data
    records_data = []
    
    # Add payments
    for payment in patient_payments:
        records_data.append({
            'id': f'payment_{payment.id}',
            'type': 'payment',
            'amount': str(payment.amount),
            'remaining_amount': '0',
            'status': 'paid',
            'payment_type': payment.payment_type,
            'payment_type_display': payment.get_payment_type_display(),
            'payment_method': payment.payment_method,
            'payment_method_display': payment.get_payment_method_display(),
            'date': payment.payment_date.strftime('%b %d, %Y at %I:%M %p'),
            'notes': payment.notes or '',
            'bill_number': f'PAY-{payment.id:06d}'
        })
    
    # Add bills
    for bill in patient_bills:
        records_data.append({
            'id': f'bill_{bill.id}',
            'type': 'bill',
            'amount': str(bill.amount),
            'paid_amount': str(bill.paid_amount),
            'remaining_amount': str(bill.remaining_amount),
            'status': bill.status,
            'payment_type': 'bill',
            'payment_type_display': bill.description,
            'payment_method': 'N/A',
            'payment_method_display': 'N/A',
            'date': bill.bill_date.strftime('%b %d, %Y at %I:%M %p'),
            'due_date': bill.due_date.strftime('%b %d, %Y'),
            'notes': bill.notes or '',
            'bill_number': bill.bill_number,
            'is_overdue': bill.is_overdue,
            'days_overdue': bill.days_overdue
        })
    
    # Sort by date (newest first)
    records_data.sort(key=lambda x: x['date'], reverse=True)
    
    return JsonResponse({
        'records': records_data,
        'total_paid': str(total_paid),
        'total_due': str(total_due),
        'count': len(records_data),
        'patient_name': patient.full_name
    })

@login_required
def create_bill(request):
    """Create a new bill for a patient"""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        messages.error(request, 'You do not have permission to create bills.')
        return redirect('patient_bills')
    
    if request.method == 'POST':
        from patients.models import Patient, PatientBill
        from datetime import datetime
        
        try:
            patient_id = request.POST.get('patient_id')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            due_date = request.POST.get('due_date')
            notes = request.POST.get('notes', '')
            
            # Validate required fields
            if not all([patient_id, description, amount, due_date]):
                messages.error(request, 'All required fields must be filled.')
                return redirect('patient_bills')
            
            # Convert and validate amount
            try:
                amount = float(amount)
                if amount <= 0:
                    messages.error(request, 'Amount must be greater than 0.')
                    return redirect('patient_bills')
            except (ValueError, TypeError):
                messages.error(request, 'Invalid amount format.')
                return redirect('patient_bills')
            
            # Get patient
            patient = Patient.objects.get(id=patient_id)
            
            # Create bill
            bill = PatientBill.objects.create(
                patient=patient,
                description=description,
                amount=amount,
                due_date=due_date,
                notes=notes,
                created_by=request.user
            )
            
            messages.success(request, f'Bill {bill.bill_number} created successfully for {patient.full_name}.')
            
        except Patient.DoesNotExist:
            messages.error(request, 'Patient not found.')
        except Exception as e:
            messages.error(request, f'Error creating bill: {str(e)}')
    
    return redirect('patient_bills')

@login_required
def get_patients(request):
    """API endpoint to get all patients for bill creation"""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    from patients.models import Patient
    
    # Get all patients, not just active ones
    patients = Patient.objects.select_related('user').order_by('user__first_name', 'user__last_name')
    
    patients_data = []
    for patient in patients:
        patients_data.append({
            'id': patient.id,
            'name': patient.full_name,
            'email': patient.user.email if patient.user else '',
            'status': patient.status if hasattr(patient, 'status') else 'active'
        })
    
    return JsonResponse({
        'patients': patients_data
    })

@login_required
def pay_bill(request, bill_id):
    """Process payment for a bill"""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin'):
        messages.error(request, 'You do not have permission to process payments.')
        return redirect('patient_bills')
    
    if request.method == 'POST':
        from patients.models import PatientBill, PatientPayment
        from django.db import transaction
        
        try:
            bill = PatientBill.objects.get(id=bill_id)
            payment_amount_str = request.POST.get('payment_amount', '0')
            payment_method = request.POST.get('payment_method')
            payment_notes = request.POST.get('payment_notes', '')
            
            # Convert to Decimal for proper handling
            from decimal import Decimal
            try:
                payment_amount = Decimal(str(payment_amount_str))
            except (ValueError, TypeError):
                messages.error(request, 'Invalid payment amount format.')
                return redirect('patient_bills')
            
            if payment_amount <= 0:
                messages.error(request, 'Payment amount must be greater than 0.')
                return redirect('patient_bills')
            
            if payment_amount > bill.remaining_amount:
                messages.error(request, 'Payment amount cannot exceed remaining balance.')
                return redirect('patient_bills')
            
            with transaction.atomic():
                # Update bill payment (both are now Decimal)
                bill.paid_amount += payment_amount
                bill.save()  # This will automatically update status
                
                # Create payment record
                PatientPayment.objects.create(
                    patient=bill.patient,
                    payment_type='bill_payment',
                    amount=payment_amount,
                    payment_method=payment_method,
                    notes=f'Payment for bill {bill.bill_number}. {payment_notes}'.strip()
                )
                
                if bill.status == 'paid':
                    messages.success(request, f'Bill {bill.bill_number} has been fully paid.')
                else:
                    messages.success(request, f'Partial payment of ${payment_amount} recorded for bill {bill.bill_number}.')
        
        except PatientBill.DoesNotExist:
            messages.error(request, 'Bill not found.')
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    return redirect('patient_bills')
