from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'emr'

urlpatterns = [
    # Dashboard
    path('', login_required(views.dashboard), name='dashboard'),
    
    # Patient Records
    path('patient/<int:pk>/record/', 
         login_required(views.PatientRecordDetailView.as_view()), 
         name='patient_record'),
    path('patient/<int:pk>/record/edit/', 
         login_required(views.PatientRecordUpdateView.as_view()), 
         name='patient_record_edit'),
    
    # Medical History
    path('patients/select/', 
         login_required(views.patient_selection), 
         name='patient_selection'),
    path('patient/<int:patient_id>/create-medical-history/', 
         login_required(views.create_medical_history), 
         name='create_medical_history'),
    path('patient/<int:patient_id>/medical-history/', 
         login_required(views.patient_medical_history), 
         name='patient_medical_history'),
    path('medical-history/', 
         login_required(views.patient_medical_history), 
         name='my_medical_history'),
    
    # Vital Signs
    path('patient/<int:pk>/vitals/add/', 
         login_required(views.VitalSignsCreateView.as_view()), 
         name='add_vitals'),
    path('patient/<int:pk>/vitals/', 
         login_required(views.VitalSignsListView.as_view()), 
         name='patient_vitals'),
    
    # Digital Forms
    path('forms/', 
         login_required(views.FormTemplateListView.as_view()), 
         name='form_templates'),
    path('forms/<int:pk>/fill/', 
         login_required(views.FormFillView.as_view()), 
         name='fill_form'),
    
    # Equipment Management
    path('equipment/', 
         login_required(views.EquipmentListView.as_view()), 
         name='equipment_list'),
    path('equipment/checkout/', 
         login_required(views.EquipmentCheckoutView.as_view()), 
         name='equipment_checkout'),
    
    # Alerts
    path('alerts/', 
         login_required(views.AlertListView.as_view()), 
         name='alerts'),
    path('alerts/<int:pk>/acknowledge/', 
         login_required(views.acknowledge_alert), 
         name='acknowledge_alert'),
    
    # Reports
    path('reports/', 
         login_required(views.ReportListView.as_view()), 
         name='reports'),
    
    # API Endpoints
    path('api/patient/<int:patient_id>/vitals/', 
         views.get_patient_vitals, 
         name='api_patient_vitals'),
    path('api/equipment/status/', 
         views.get_equipment_status, 
         name='api_equipment_status'),
    
    # Medical History Management APIs
    path('api/medical-record/add/', 
         views.add_medical_record_api, 
         name='add_medical_record_api'),
    path('api/medical-record/edit/', 
         views.edit_medical_record_api, 
         name='edit_medical_record_api'),
    path('api/allergy/add/', 
         views.add_allergy_api, 
         name='add_allergy_api'),
    path('api/medication/add/', 
         views.add_medication_api, 
         name='add_medication_api'),
    path('api/record/delete/', 
         views.delete_record_api, 
         name='delete_record_api'),
    path('api/field/update/', 
         views.update_field_api, 
         name='update_field_api'),
]
