from django.urls import path
from . import views

app_name = 'blood_bank'

urlpatterns = [
    # Web pages
    path('', views.dashboard, name='dashboard'),  # Blood bank dashboard
    path('donors/', views.donors_list, name='donors_list'),
    path('transfers/', views.transfers_list, name='transfers_list'),
    
    # API endpoints
    path('api/statistics/', views.donor_statistics_api, name='donor_statistics_api'),
    path('api/inventory/', views.blood_inventory_api, name='blood_inventory_api'),
    path('api/compatibility/', views.blood_compatibility_api, name='blood_compatibility_api'),
    path('api/add-donor/', views.add_donor_api, name='add_donor_api'),
    path('api/donor/<int:donor_id>/', views.get_donor_details_api, name='get_donor_details_api'),
    path('api/all-donors/', views.get_all_donors_api, name='get_all_donors_api'),
    path('api/update-donor/', views.update_donor_api, name='update_donor_api'),
    path('api/delete-donor/', views.delete_donor_api, name='delete_donor_api'),
    path('api/add-transfer/', views.add_transfer_api, name='add_transfer_api'),
    path('api/transfers/', views.get_transfers_api, name='get_transfers_api'),
]
