from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('', views.prescription_list, name='list'),
    path('create/', views.create_prescription, name='create'),
    path('<int:pk>/', views.prescription_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_prescription, name='edit'),
    path('<int:pk>/delete/', views.delete_prescription, name='delete'),
]
