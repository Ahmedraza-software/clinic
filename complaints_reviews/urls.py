from django.urls import path
from . import views

app_name = 'complaints_reviews'

urlpatterns = [
    path('', views.complaints_reviews_list, name='list'),
    path('create/', views.create_complaint_review, name='create'),
    path('<int:pk>/', views.complaint_review_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_complaint_review, name='edit'),
    path('<int:pk>/delete/', views.delete_complaint_review, name='delete'),
]
