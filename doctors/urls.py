from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.doctor_list, name='list'),  # List all doctors
    path('add/', views.add_doctor, name='add'),  # Add new doctor (admin only)
    path('<int:pk>/', views.doctor_detail, name='detail'),  # Doctor detail (admin only)
    path('<int:pk>/edit/', views.doctor_edit, name='edit'),  # Edit doctor (admin only)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('schedule/', views.schedule, name='schedule'),
    path('patients/', views.patient_list, name='patient_list'),
]
