from django.urls import path
from . import views
from .views_ot import ot_dashboard

app_name = 'operation_theater'

urlpatterns = [
    # Dashboard
    path('', ot_dashboard, name='dashboard'),
    
    # Surgery URLs
    path('surgeries/', views.SurgeryListView.as_view(), name='surgery_list'),
    path('surgeries/add/', views.SurgeryCreateView.as_view(), name='surgery_add'),
    path('surgeries/<int:pk>/', views.SurgeryDetailView.as_view(), name='surgery_detail'),
    path('surgeries/<int:pk>/edit/', views.SurgeryUpdateView.as_view(), name='surgery_edit'),
    path('surgeries/<int:pk>/delete/', views.SurgeryDeleteView.as_view(), name='surgery_delete'),
    path('surgeries/<int:surgery_id>/update-status/', views.update_surgery_status, name='update_surgery_status'),
    path('surgeries/<int:surgery_id>/update-notes/', views.update_surgery_notes, name='update_surgery_notes'),
    
    # Team Member URLs
    path('surgeries/<int:surgery_id>/add-team-member/', views.add_team_member, name='add_team_member'),
    path('team-members/<int:team_member_id>/remove/', views.remove_team_member, name='remove_team_member'),
    
    # Consumables URLs
    path('surgeries/<int:surgery_id>/add-consumable/', views.add_consumable, name='add_consumable'),
    
    # Operation Theater URLs
    path('operation-theaters/', views.OperationTheaterListView.as_view(), name='ot_list'),
    path('operation-theaters/add/', views.OperationTheaterCreateView.as_view(), name='ot_add'),
    path('operation-theaters/<int:pk>/edit/', views.OperationTheaterUpdateView.as_view(), name='ot_edit'),
    path('operation-theaters/<int:pk>/delete/', views.OperationTheaterDeleteView.as_view(), name='ot_delete'),
    
    # Surgery Type URLs
    path('surgery-types/', views.SurgeryTypeListView.as_view(), name='surgery_type_list'),
    path('surgery-types/add/', views.SurgeryTypeCreateView.as_view(), name='surgery_type_add'),
    path('surgery-types/<int:pk>/edit/', views.SurgeryTypeUpdateView.as_view(), name='surgery_type_edit'),
    
    # Calendar and AJAX
    path('calendar/', views.ot_calendar, name='ot_calendar'),
    path('api/available-time-slots/', views.get_available_time_slots, name='available_time_slots'),
    path('api/calendar-events/', views.get_calendar_events, name='calendar_events'),
]
