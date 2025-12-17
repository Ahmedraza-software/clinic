"""
URL configuration for clinic_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

# Customize Django Admin Site
admin.site.site_header = "Clinic Management System - Admin"
admin.site.site_title = "Clinic Management System"
admin.site.index_title = "Welcome to Clinic Management System"

urlpatterns = [
    # Main URLs
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/revenue-details/', views.revenue_details, name='revenue_details'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/', include('accounts.urls')),
    
    # App-specific URLs
    path('appointments/', include('appointments.urls')),
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('emr/', include('emr.urls', namespace='emr')),
    
    # Operation Theater
    path('ot-management/', include('operation_theater.urls', namespace='operation_theater')),
    # Blood Bank
    path('blood-bank/', include('blood_bank.urls', namespace='blood_bank')),
    path('blood-bank/transfer/', views.blood_transfer, name='blood_transfer'),
    path('patient/medical-history/<int:patient_id>/', views.patient_medical_history, name='patient_medical_history'),
    
    # Billing & Finance
    path('billing/patient-bills/', views.patient_bills, name='patient_bills'),
    path('billing/export-patient-bills/', views.export_patient_bills, name='export_patient_bills'),
    path('billing/patient-payments/<int:patient_id>/', views.patient_payments, name='patient_payments'),
    path('billing/create-bill/', views.create_bill, name='create_bill'),
    path('billing/get-patients/', views.get_patients, name='get_patients'),
    path('billing/pay-bill/<int:bill_id>/', views.pay_bill, name='pay_bill'),
    path('billing/consultation-fees/', views.consultation_fees, name='consultation_fees'),
    path('api/create-appointment/', views.create_appointment_api, name='create_appointment_api'),
    path('finance/accounts/', views.accounts_finance, name='accounts_finance'),
    path('finance/expenses/', views.expenses, name='expenses'),
    path('finance/get-expense/<int:expense_id>/', views.get_expense, name='get_expense'),
    path('finance/delete-expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('finance/pay-doctor/', views.pay_doctor, name='pay_doctor'),
    path('finance/refresh-data/', views.refresh_financial_data, name='refresh_financial_data'),
    path('finance/transactions/', views.transactions, name='transactions'),
    
    # Management
    path('inventory/', include('inventory.urls')),
    path('complaints-reviews/', include('complaints_reviews.urls', namespace='complaints_reviews')),
    path('reviews/', views.patient_reviews, name='patient_reviews'),
    path('complaints/', views.complaints, name='complaints'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
