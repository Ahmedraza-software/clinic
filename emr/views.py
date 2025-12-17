from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    PatientMedicalRecord, VitalSigns, DigitalFormTemplate, FilledForm,
    Equipment, EquipmentCheckout, Alert, AlertRule, ReportTemplate, GeneratedReport,
    MedicalHistoryRecord, PatientAllergy, PatientMedication
)
from patients.models import Patient
from accounts.models import CustomUser

# Helper function to check if user is staff
def is_staff(user):
    return user.is_staff

# Dashboard View
@login_required
def dashboard(request):
    context = {
        'title': 'EMR Dashboard',
        'active_page': 'emr_dashboard',
    }
    
    if request.user.user_type == 'doctor':
        # Doctor-specific dashboard data
        context['recent_patients'] = Patient.objects.filter(
            appointment__doctor__user=request.user
        ).distinct()[:5]
        context['recent_alerts'] = Alert.objects.filter(
            patient__in=Patient.objects.filter(appointment__doctor__user=request.user)
        ).order_by('-created_at')[:5]
    
    elif request.user.user_type == 'patient':
        # Patient-specific dashboard data
        try:
            patient = Patient.objects.get(user=request.user)
            context['recent_vitals'] = VitalSigns.objects.filter(patient=patient).order_by('-recorded_at')[:5]
            context['recent_forms'] = FilledForm.objects.filter(patient=patient).order_by('-created_at')[:5]
            context['active_medications'] = patient.current_medications.split('\n') if patient.current_medications else []
        except Patient.DoesNotExist:
            pass
    
    return render(request, 'emr/dashboard.html', context)

# Patient Medical Records
class PatientRecordDetailView(LoginRequiredMixin, DetailView):
    model = PatientMedicalRecord
    template_name = 'emr/patient_record_detail.html'
    context_object_name = 'record'
    
    def get_queryset(self):
        if self.request.user.user_type == 'patient':
            return PatientMedicalRecord.objects.filter(patient__user=self.request.user)
        return PatientMedicalRecord.objects.all()

class PatientRecordUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PatientMedicalRecord
    fields = ['blood_type', 'allergies', 'medical_history', 'current_medications', 'family_history', 'notes']
    template_name = 'emr/patient_record_form.html'
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Patient record has been updated.')
        return super().form_valid(form)
    
    def test_func(self):
        if self.request.user.user_type in ['doctor', 'admin']:
            return True
        return self.get_object().patient.user == self.request.user

# Vital Signs
class VitalSignsCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = VitalSigns
    fields = [
        'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic',
        'heart_rate', 'respiratory_rate', 'oxygen_saturation',
        'weight', 'height', 'notes'
    ]
    template_name = 'emr/vitals_form.html'
    
    def form_valid(self, form):
        form.instance.patient = get_object_or_404(Patient, pk=self.kwargs.get('pk'))
        form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Vital signs have been recorded.')
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.user_type in ['doctor', 'nurse']

class VitalSignsListView(LoginRequiredMixin, ListView):
    model = VitalSigns
    template_name = 'emr/vitals_list.html'
    context_object_name = 'vitals'
    paginate_by = 10
    
    def get_queryset(self):
        patient_id = self.kwargs.get('pk')
        patient = get_object_or_404(Patient, pk=patient_id)
        
        if self.request.user.user_type == 'patient' and patient.user != self.request.user:
            return VitalSigns.objects.none()
            
        return VitalSigns.objects.filter(patient=patient).order_by('-recorded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = get_object_or_404(Patient, pk=self.kwargs.get('pk'))
        return context

# Digital Forms
class FormTemplateListView(LoginRequiredMixin, ListView):
    model = DigitalFormTemplate
    template_name = 'emr/form_templates.html'
    context_object_name = 'templates'
    
    def get_queryset(self):
        return DigitalFormTemplate.objects.filter(is_active=True)

class FormFillView(LoginRequiredMixin, CreateView):
    model = FilledForm
    fields = ['form_data']
    template_name = 'emr/fill_form.html'
    
    def get_template(self):
        return get_object_or_404(DigitalFormTemplate, pk=self.kwargs.get('pk'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template'] = self.get_template()
        return context
    
    def form_valid(self, form):
        form.instance.template = self.get_template()
        form.instance.patient = self.request.user.patient_profile
        form.instance.filled_by = self.request.user
        messages.success(self.request, 'Form has been submitted successfully.')
        return super().form_valid(form)

# Equipment Management
class EquipmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Equipment
    template_name = 'emr/equipment_list.html'
    context_object_name = 'equipment_list'
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'staff']

class EquipmentCheckoutView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = EquipmentCheckout
    fields = ['equipment', 'patient', 'expected_return', 'condition_out', 'notes']
    template_name = 'emr/equipment_checkout.html'
    success_url = reverse_lazy('equipment-list')
    
    def form_valid(self, form):
        form.instance.checked_out_by = self.request.user
        messages.success(self.request, 'Equipment has been checked out.')
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'staff', 'nurse']

# Alerts
class AlertListView(LoginRequiredMixin, ListView):
    model = Alert
    template_name = 'emr/alerts.html'
    context_object_name = 'alerts'
    paginate_by = 10
    
    def get_queryset(self):
        if self.request.user.user_type == 'patient':
            return Alert.objects.filter(patient__user=self.request.user, is_acknowledged=False)
        elif self.request.user.user_type == 'doctor':
            return Alert.objects.filter(
                Q(patient__appointment__doctor__user=self.request.user) | 
                Q(alert_type='equipment_due')
            ).distinct()
        return Alert.objects.all()

@login_required
def acknowledge_alert(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if request.method == 'POST':
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        messages.success(request, 'Alert has been acknowledged.')
    return redirect('alerts')

# Reports
class ReportListView(LoginRequiredMixin, ListView):
    model = GeneratedReport
    template_name = 'emr/reports.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        if self.request.user.user_type == 'patient':
            return GeneratedReport.objects.filter(patient__user=self.request.user)
        return GeneratedReport.objects.all()

# API Views
def get_patient_vitals(request, patient_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        patient = Patient.objects.get(pk=patient_id)
        if request.user.user_type == 'patient' and patient.user != request.user:
            return JsonResponse({'error': 'Not authorized'}, status=403)
            
        vitals = VitalSigns.objects.filter(patient=patient).order_by('-recorded_at')[:10]
        data = [{
            'date': v.recorded_at.strftime('%Y-%m-%d %H:%M'),
            'temperature': float(v.temperature) if v.temperature else None,
            'systolic': v.blood_pressure_systolic,
            'diastolic': v.blood_pressure_diastolic,
            'heart_rate': v.heart_rate,
            'oxygen': v.oxygen_saturation,
        } for v in vitals]
        
        return JsonResponse({'vitals': data})
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_equipment_status(request):
    if not request.user.is_authenticated or request.user.user_type not in ['admin', 'staff']:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    equipment = Equipment.objects.all()
    data = [{
        'id': e.id,
        'name': e.name,
        'type': e.get_equipment_type_display(),
        'status': e.status,
        'location': e.location or 'N/A',
        'last_maintenance': e.last_maintenance.strftime('%Y-%m-%d') if e.last_maintenance else 'N/A',
        'next_maintenance': e.next_maintenance.strftime('%Y-%m-%d') if e.next_maintenance else 'N/A',
        'is_overdue': e.next_maintenance and e.next_maintenance < timezone.now().date()
    } for e in equipment]
    
    return JsonResponse({'equipment': data})

# Medical History View
@login_required
def patient_medical_history(request, patient_id=None):
    """Comprehensive patient medical history view"""
    
    # If no patient_id provided, try to get from current user or show selection
    if not patient_id:
        if hasattr(request.user, 'patient_profile'):
            patient = request.user.patient_profile
        else:
            # For staff/doctors, redirect to patient selection or show error
            messages.error(request, 'Please select a patient to view medical history.')
            return redirect('dashboard')
    else:
        try:
            patient = Patient.objects.get(pk=patient_id)
            
            # Check permissions
            if request.user.user_type == 'patient' and patient.user != request.user:
                messages.error(request, 'You can only view your own medical history.')
                return redirect('dashboard')
                
        except Patient.DoesNotExist:
            messages.error(request, 'Patient not found.')
            return redirect('dashboard')
    
    # Get medical history records
    medical_records = MedicalHistoryRecord.objects.filter(
        patient=patient
    ).order_by('-date', '-time')[:20]  # Last 20 records
    
    # Get allergies
    allergies = PatientAllergy.objects.filter(
        patient=patient,
        is_active=True
    ).order_by('-severity', 'allergen')
    
    # Get current medications
    medications = PatientMedication.objects.filter(
        patient=patient,
        status='active'
    ).order_by('medication_name')
    
    # Get last visit date
    last_visit = None
    if medical_records.exists():
        last_visit = medical_records.first().date
    
    # Get available doctors for the dropdown
    from doctors.models import Doctor
    doctors = Doctor.objects.filter(is_available=True).select_related('user').order_by('user__first_name')
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'allergies': allergies,
        'medications': medications,
        'last_visit': last_visit,
        'doctors': doctors,
        'active_page': 'medical_history',
        'page_title': f'Medical History - {patient.full_name}',
        'user_can_edit': request.user.is_staff or request.user.is_superuser,
    }
    
    return render(request, 'emr/medical_history.html', context)

# Patient Selection View for Admin
@login_required
def patient_selection(request):
    """Patient selection page for admin/staff to choose patient for medical history"""
    
    # Check if user has permission to view all patients
    if not (request.user.is_staff or request.user.is_superuser or 
            getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get all patients
    patients = Patient.objects.select_related('user').filter(is_active=True)
    
    # Apply search filter if provided
    if search_query:
        patients = patients.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Order by most recent first
    patients = patients.order_by('-created_at')
    
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
        'active_page': 'patient_selection',
        'page_title': 'Select Patient - Medical History',
        'page_obj': patients_page,
        'paginator': paginator,
    }
    
    return render(request, 'emr/patient_selection.html', context)

# Create Medical History View
@login_required
def create_medical_history(request, patient_id):
    """Create initial medical history for a new patient"""
    
    # Check permissions
    if not (request.user.is_staff or request.user.is_superuser or 
            getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
        messages.error(request, 'You do not have permission to create medical history.')
        return redirect('emr:patient_selection')
    
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient not found.')
        return redirect('emr:patient_selection')
    
    # Check if patient already has medical history
    if patient.has_medical_history:
        messages.info(request, f'{patient.full_name} already has medical history.')
        return redirect('emr:patient_medical_history', patient_id=patient.id)
    
    if request.method == 'POST':
        try:
            # Process the form data
            conditions = request.POST.getlist('conditions')
            allergies = request.POST.getlist('allergies')
            medications = request.POST.getlist('medications')
            family_history = request.POST.get('family_history', '')
            additional_notes = request.POST.get('additional_notes', '')
            
            # Predefined condition mappings
            condition_mappings = {
                'hypertension': {
                    'type': 'consultation',
                    'diagnosis': 'Hypertension (High Blood Pressure)',
                    'doctor': 'Dr. Initial Assessment'
                },
                'diabetes': {
                    'type': 'consultation',
                    'diagnosis': 'Diabetes Mellitus',
                    'doctor': 'Dr. Initial Assessment'
                },
                'asthma': {
                    'type': 'consultation',
                    'diagnosis': 'Asthma',
                    'doctor': 'Dr. Initial Assessment'
                },
                'heart_disease': {
                    'type': 'consultation',
                    'diagnosis': 'Heart Disease',
                    'doctor': 'Dr. Initial Assessment'
                },
                'arthritis': {
                    'type': 'consultation',
                    'diagnosis': 'Arthritis',
                    'doctor': 'Dr. Initial Assessment'
                },
                'depression': {
                    'type': 'consultation',
                    'diagnosis': 'Depression/Anxiety Disorder',
                    'doctor': 'Dr. Initial Assessment'
                },
                'migraine': {
                    'type': 'consultation',
                    'diagnosis': 'Migraine Headaches',
                    'doctor': 'Dr. Initial Assessment'
                },
                'thyroid': {
                    'type': 'consultation',
                    'diagnosis': 'Thyroid Disorder',
                    'doctor': 'Dr. Initial Assessment'
                }
            }
            
            # Allergy mappings
            allergy_mappings = {
                'penicillin': {
                    'allergen': 'Penicillin',
                    'type': 'drug',
                    'severity': 'severe',
                    'reaction': 'Severe skin rash, difficulty breathing, swelling'
                },
                'peanuts': {
                    'allergen': 'Peanuts',
                    'type': 'food',
                    'severity': 'moderate',
                    'reaction': 'Swelling, hives, stomach upset'
                },
                'shellfish': {
                    'allergen': 'Shellfish',
                    'type': 'food',
                    'severity': 'moderate',
                    'reaction': 'Hives, swelling, digestive issues'
                },
                'latex': {
                    'allergen': 'Latex',
                    'type': 'contact',
                    'severity': 'mild',
                    'reaction': 'Skin irritation, rash'
                },
                'dust_mites': {
                    'allergen': 'Dust Mites',
                    'type': 'environmental',
                    'severity': 'mild',
                    'reaction': 'Sneezing, runny nose, watery eyes'
                },
                'pollen': {
                    'allergen': 'Pollen',
                    'type': 'environmental',
                    'severity': 'mild',
                    'reaction': 'Seasonal allergies, sneezing, congestion'
                },
                'eggs': {
                    'allergen': 'Eggs',
                    'type': 'food',
                    'severity': 'moderate',
                    'reaction': 'Digestive upset, skin reactions'
                },
                'milk': {
                    'allergen': 'Milk/Dairy',
                    'type': 'food',
                    'severity': 'mild',
                    'reaction': 'Lactose intolerance, digestive issues'
                }
            }
            
            # Medication mappings
            medication_mappings = {
                'lisinopril': {
                    'name': 'Lisinopril',
                    'dosage': '10mg',
                    'frequency': 'once_daily',
                    'indication': 'For high blood pressure',
                    'doctor': 'Dr. Initial Assessment'
                },
                'metformin': {
                    'name': 'Metformin',
                    'dosage': '500mg',
                    'frequency': 'twice_daily',
                    'indication': 'For diabetes management',
                    'doctor': 'Dr. Initial Assessment'
                },
                'atorvastatin': {
                    'name': 'Atorvastatin',
                    'dosage': '20mg',
                    'frequency': 'once_daily',
                    'indication': 'For high cholesterol',
                    'doctor': 'Dr. Initial Assessment'
                },
                'albuterol': {
                    'name': 'Albuterol',
                    'dosage': '90mcg',
                    'frequency': 'as_needed',
                    'indication': 'For asthma symptoms',
                    'doctor': 'Dr. Initial Assessment'
                },
                'omeprazole': {
                    'name': 'Omeprazole',
                    'dosage': '20mg',
                    'frequency': 'once_daily',
                    'indication': 'For acid reflux',
                    'doctor': 'Dr. Initial Assessment'
                },
                'ibuprofen': {
                    'name': 'Ibuprofen',
                    'dosage': '200mg',
                    'frequency': 'as_needed',
                    'indication': 'For pain and inflammation',
                    'doctor': 'Dr. Initial Assessment'
                },
                'levothyroxine': {
                    'name': 'Levothyroxine',
                    'dosage': '50mcg',
                    'frequency': 'once_daily',
                    'indication': 'For thyroid hormone replacement',
                    'doctor': 'Dr. Initial Assessment'
                },
                'multivitamin': {
                    'name': 'Multivitamin',
                    'dosage': '1 tablet',
                    'frequency': 'once_daily',
                    'indication': 'For nutritional supplementation',
                    'doctor': 'Dr. Initial Assessment'
                }
            }
            
            # Create medical records for selected conditions
            for condition in conditions:
                if condition in condition_mappings:
                    mapping = condition_mappings[condition]
                    MedicalHistoryRecord.objects.create(
                        patient=patient,
                        record_type=mapping['type'],
                        date=timezone.now().date(),
                        time=timezone.now().time(),
                        doctor_name=mapping['doctor'],
                        diagnosis=mapping['diagnosis'],
                        treatment='Initial assessment and management plan',
                        notes=f'Condition identified during initial medical history setup. {additional_notes}',
                        status='completed'
                    )
            
            # Create allergies for selected items
            for allergy in allergies:
                if allergy in allergy_mappings:
                    mapping = allergy_mappings[allergy]
                    PatientAllergy.objects.create(
                        patient=patient,
                        allergen=mapping['allergen'],
                        allergy_type=mapping['type'],
                        severity=mapping['severity'],
                        reaction=mapping['reaction'],
                        date_identified=timezone.now().date(),
                        is_active=True
                    )
            
            # Create medications for selected items
            for medication in medications:
                if medication in medication_mappings:
                    mapping = medication_mappings[medication]
                    PatientMedication.objects.create(
                        patient=patient,
                        medication_name=mapping['name'],
                        dosage=mapping['dosage'],
                        frequency=mapping['frequency'],
                        route='Oral',
                        indication=mapping['indication'],
                        prescribed_by_name=mapping['doctor'],
                        start_date=timezone.now().date(),
                        status='active'
                    )
            
            # Create initial consultation record if family history or notes provided
            if family_history or additional_notes:
                MedicalHistoryRecord.objects.create(
                    patient=patient,
                    record_type='consultation',
                    date=timezone.now().date(),
                    time=timezone.now().time(),
                    doctor_name='Dr. Initial Assessment',
                    diagnosis='Initial Medical History Assessment',
                    treatment='Medical history documented and reviewed',
                    notes=f'Family History: {family_history}\n\nAdditional Notes: {additional_notes}',
                    status='completed'
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Medical history created successfully!',
                'redirect_url': f'/emr/patient/{patient.id}/medical-history/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating medical history: {str(e)}'
            })
    
    context = {
        'patient': patient,
        'active_page': 'create_medical_history',
        'page_title': f'Create Medical History - {patient.full_name}',
    }
    
    return render(request, 'emr/create_medical_history.html', context)

# API Endpoints for Medical History Management

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def add_medical_record_api(request):
    """API endpoint to add a new medical record"""
    try:
        # Check permissions
        if not (request.user.is_staff or request.user.is_superuser or 
                getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        data = request.POST
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return JsonResponse({'success': False, 'message': 'Patient ID is required'}, status=400)
        
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Parse date
        from datetime import datetime
        date_str = data.get('date')
        if date_str:
            try:
                record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                record_date = timezone.now().date()
        else:
            record_date = timezone.now().date()
        
        # Get doctor information
        doctor_user = None
        doctor_name = 'Unknown Doctor'
        
        doctor_id = data.get('doctor_id')
        if doctor_id:
            try:
                from doctors.models import Doctor
                doctor_obj = Doctor.objects.select_related('user').get(id=doctor_id)
                doctor_user = doctor_obj.user  # Get the CustomUser instance
                doctor_name = doctor_obj.full_name
            except Doctor.DoesNotExist:
                doctor_name = 'Unknown Doctor'
        
        # Create medical record
        record = MedicalHistoryRecord.objects.create(
            patient=patient,
            record_type=data.get('record_type'),
            date=record_date,
            time=data.get('time') or timezone.now().time(),
            doctor=doctor_user,  # Assign the CustomUser instance, not Doctor instance
            doctor_name=doctor_name,
            diagnosis=data.get('diagnosis'),
            treatment=data.get('treatment', ''),
            notes=data.get('notes', ''),
            status=data.get('status', 'completed'),
            follow_up_required=data.get('follow_up_required') == 'true',
            follow_up_date=data.get('follow_up_date') if data.get('follow_up_date') else None
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Medical record added successfully',
            'record': {
                'id': record.id,
                'date': record.date.strftime('%b %d, %Y'),
                'record_type': record.record_type,
                'doctor_name': record.doctor_name,
                'diagnosis': record.diagnosis,
                'status': record.status
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def add_allergy_api(request):
    """API endpoint to add a new allergy"""
    try:
        # Check permissions
        if not (request.user.is_staff or request.user.is_superuser or 
                getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        data = request.POST
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return JsonResponse({'success': False, 'message': 'Patient ID is required'}, status=400)
        
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Parse date for allergy
        from datetime import datetime
        date_identified = None
        if data.get('date_identified'):
            try:
                date_identified = datetime.strptime(data.get('date_identified'), '%Y-%m-%d').date()
            except ValueError:
                date_identified = None
        
        # Create allergy
        allergy = PatientAllergy.objects.create(
            patient=patient,
            allergen=data.get('allergen'),
            allergy_type=data.get('allergy_type'),
            severity=data.get('severity'),
            reaction=data.get('reaction'),
            date_identified=date_identified,
            notes=data.get('notes', ''),
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Allergy added successfully',
            'allergy': {
                'id': allergy.id,
                'allergen': allergy.allergen,
                'severity': allergy.get_severity_display(),
                'allergy_type': allergy.get_allergy_type_display(),
                'reaction': allergy.reaction
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def add_medication_api(request):
    """API endpoint to add a new medication"""
    try:
        # Check permissions
        if not (request.user.is_staff or request.user.is_superuser or 
                getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        data = request.POST
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return JsonResponse({'success': False, 'message': 'Patient ID is required'}, status=400)
        
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Parse dates for medication
        from datetime import datetime
        start_date = timezone.now().date()
        if data.get('start_date'):
            try:
                start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            except ValueError:
                start_date = timezone.now().date()
        
        end_date = None
        if data.get('end_date'):
            try:
                end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        
        # Get prescribing doctor information
        prescribed_by_user = None
        prescribed_by_name = 'Unknown Doctor'
        
        prescribed_by_id = data.get('prescribed_by_id')
        if prescribed_by_id:
            try:
                from doctors.models import Doctor
                prescribed_by_obj = Doctor.objects.select_related('user').get(id=prescribed_by_id)
                prescribed_by_user = prescribed_by_obj.user  # Get the CustomUser instance
                prescribed_by_name = prescribed_by_obj.full_name
            except Doctor.DoesNotExist:
                prescribed_by_name = 'Unknown Doctor'
        
        # Create medication
        medication = PatientMedication.objects.create(
            patient=patient,
            medication_name=data.get('medication_name'),
            dosage=data.get('dosage'),
            frequency=data.get('frequency'),
            route=data.get('route', 'Oral'),
            indication=data.get('indication'),
            prescribed_by=prescribed_by_user,  # Assign the CustomUser instance
            prescribed_by_name=prescribed_by_name,
            start_date=start_date,
            end_date=end_date,
            status=data.get('status', 'active'),
            notes=data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Medication added successfully',
            'medication': {
                'id': medication.id,
                'medication_name': medication.medication_name,
                'dosage': medication.dosage,
                'frequency': medication.get_frequency_display(),
                'indication': medication.indication,
                'prescribed_by_name': medication.prescribed_by_name
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def edit_medical_record_api(request):
    """API endpoint to edit a medical record"""
    try:
        # Check permissions
        if not (request.user.is_staff or request.user.is_superuser or 
                getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        data = request.POST
        record_id = data.get('record_id')
        
        if not record_id:
            return JsonResponse({'success': False, 'message': 'Record ID is required'}, status=400)
        
        record = get_object_or_404(MedicalHistoryRecord, id=record_id)
        
        # Update record
        record.record_type = data.get('record_type', record.record_type)
        record.date = data.get('date', record.date)
        record.time = data.get('time', record.time)
        record.doctor_name = data.get('doctor_name', record.doctor_name)
        record.diagnosis = data.get('diagnosis', record.diagnosis)
        record.treatment = data.get('treatment', record.treatment)
        record.notes = data.get('notes', record.notes)
        record.status = data.get('status', record.status)
        record.follow_up_required = data.get('follow_up_required') == 'true'
        if data.get('follow_up_date'):
            record.follow_up_date = data.get('follow_up_date')
        
        record.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Medical record updated successfully',
            'record': {
                'id': record.id,
                'date': record.date.strftime('%Y-%m-%d'),
                'record_type': record.get_record_type_display(),
                'doctor_name': record.doctor_name,
                'diagnosis': record.diagnosis,
                'status': record.get_status_display()
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def delete_record_api(request):
    """API endpoint to delete medical records, allergies, or medications"""
    try:
        # Check permissions
        if not (request.user.is_staff or request.user.is_superuser or 
                getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        data = request.POST
        record_type = data.get('record_type')  # 'medical_record', 'allergy', 'medication'
        record_id = data.get('record_id')
        
        if not record_type or not record_id:
            return JsonResponse({'success': False, 'message': 'Record type and ID are required'}, status=400)
        
        if record_type == 'medical_record':
            record = get_object_or_404(MedicalHistoryRecord, id=record_id)
            record.delete()
            message = 'Medical record deleted successfully'
        elif record_type == 'allergy':
            record = get_object_or_404(PatientAllergy, id=record_id)
            record.delete()
            message = 'Allergy deleted successfully'
        elif record_type == 'medication':
            record = get_object_or_404(PatientMedication, id=record_id)
            record.delete()
            message = 'Medication deleted successfully'
        else:
            return JsonResponse({'success': False, 'message': 'Invalid record type'}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def update_field_api(request):
    """API endpoint to update a single field in medical records, allergies, or medications"""
    try:
        # Check permissions
        if not (request.user.is_staff or request.user.is_superuser or 
                getattr(request.user, 'user_type', None) in ['admin', 'doctor', 'nurse']):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        data = request.POST
        record_type = data.get('record_type')
        record_id = data.get('record_id')
        field_name = data.get('field_name')
        field_value = data.get('field_value')
        
        if not all([record_type, record_id, field_name]):
            return JsonResponse({'success': False, 'message': 'Missing required parameters'}, status=400)
        
        # Update the appropriate model
        if record_type == 'medical_record':
            record = get_object_or_404(MedicalHistoryRecord, id=record_id)
            if hasattr(record, field_name):
                setattr(record, field_name, field_value)
                record.save()
        elif record_type == 'allergy':
            record = get_object_or_404(PatientAllergy, id=record_id)
            if hasattr(record, field_name):
                setattr(record, field_name, field_value)
                record.save()
        elif record_type == 'medication':
            record = get_object_or_404(PatientMedication, id=record_id)
            if hasattr(record, field_name):
                setattr(record, field_name, field_value)
                record.save()
        else:
            return JsonResponse({'success': False, 'message': 'Invalid record type'}, status=400)
        
        # Get display value for certain fields
        display_value = field_value
        css_class = None
        
        if field_name in ['record_type', 'status', 'severity', 'allergy_type', 'frequency']:
            if hasattr(record, f'get_{field_name}_display'):
                display_value = getattr(record, f'get_{field_name}_display')()
            css_class = field_value
        elif field_name in ['date', 'start_date', 'date_identified']:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(field_value, '%Y-%m-%d')
                display_value = date_obj.strftime('%b %j, %Y')
            except:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Field updated successfully',
            'display_value': display_value,
            'css_class': css_class
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
