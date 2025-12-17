from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('medical-history/', views.medical_history, name='medical_history'),
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('import/', views.import_patients_csv, name='import_patients_csv'),  # CSV import
    path('', views.patient_list, name='list'),  # Admin-only patient list
    path('all/', views.patient_list, name='patient_list'),  # Admin-only patient list
    path('add/', views.add_patient, name='add'),  # Add new patient
    path('<int:pk>/', views.patient_detail, name='detail'),  # Patient detail view
    path('<int:pk>/edit/', views.patient_edit, name='edit'),  # Patient edit view (admin only)
    path('<int:pk>/discharge/', views.discharge_patient, name='discharge'),  # Discharge patient (admin only)
    path('<int:pk>/reactivate/', views.reactivate_patient, name='reactivate'),  # Reactivate patient (admin only)
]
