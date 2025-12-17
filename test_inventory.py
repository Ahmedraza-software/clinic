#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from inventory.models import Item, Category, Supplier, StockMovement
from accounts.models import CustomUser
from decimal import Decimal

# Create a test item
def create_test_item():
    # Get or create a category
    category, _ = Category.objects.get_or_create(
        name='Test Category',
        defaults={'description': 'Test category for testing'}
    )
    
    # Get or create a supplier
    supplier, _ = Supplier.objects.get_or_create(
        name='Test Supplier',
        defaults={
            'contact_person': 'Test Person',
            'email': 'test@example.com',
            'phone': '123-456-7890',
            'address': 'Test Address'
        }
    )
    
    # Create test item
    item, created = Item.objects.get_or_create(
        name='Test Item',
        defaults={
            'description': 'Test item for testing stock updates',
            'category': category,
            'supplier': supplier,
            'unit': 'pieces',
            'price_per_unit': Decimal('10.00'),
            'quantity_in_stock': 100,
            'minimum_quantity': 10,
            'location': 'Test Location',
            'barcode': 'TEST123'
        }
    )
    
    if created:
        print(f"Created test item: {item.name}")
        
        # Create initial stock movement
        user = CustomUser.objects.filter(is_superuser=True).first()
        if user:
            StockMovement.objects.create(
                item=item,
                movement_type='IN',
                quantity=100,
                reference='Initial Stock',
                notes='Test item creation',
                created_by=user
            )
            print("Created initial stock movement")
    else:
        print(f"Test item already exists: {item.name}")
    
    return item

if __name__ == '__main__':
    item = create_test_item()
    print(f"Test item ID: {item.id}")
    print(f"Current stock: {item.quantity_in_stock}")
    print(f"Stock movements: {item.movements.count()}")
