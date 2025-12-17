from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='dashboard'),
    path('add/', views.add_item, name='add_item'),
    path('update-stock/<int:item_id>/', views.update_stock, name='update_stock'),
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('expiry/', views.expiry_report, name='expiry_report'),
    path('movements/<int:item_id>/', views.stock_movements, name='stock_movements'),
    path('export/', views.export_inventory, name='export_inventory'),
]
