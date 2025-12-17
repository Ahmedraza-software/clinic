from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='list'),
    path('book/', views.book_appointment, name='book'),
    path('book/doctor/<int:doctor_id>/', views.book_doctor_appointment, name='book_doctor'),
    path('<int:pk>/', views.appointment_detail, name='detail'),
    path('<int:pk>/cancel/', views.cancel_appointment, name='cancel'),
    path('create/', views.create_appointment, name='create'),
    path('edit/<int:pk>/', views.edit_appointment, name='edit'),
]
