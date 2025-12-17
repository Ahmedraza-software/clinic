from django.core.management.base import BaseCommand
from inventory.models import Category, Supplier, Item, StockMovement
from decimal import Decimal
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Populate inventory with practical medical items'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                '\n🏥 POPULATING MEDICAL INVENTORY\n'
                '===============================\n'
            )
        )

        # Clear existing data
        Item.objects.all().delete()
        Category.objects.all().delete()
        Supplier.objects.all().delete()
        
        # Create categories
        categories_data = [
            {'name': 'Medications', 'description': 'Prescription and over-the-counter medications'},
            {'name': 'Medical Supplies', 'description': 'Disposable medical supplies and consumables'},
            {'name': 'Equipment', 'description': 'Medical equipment and instruments'},
            {'name': 'Laboratory', 'description': 'Laboratory supplies and reagents'},
            {'name': 'Emergency', 'description': 'Emergency medical supplies'},
            {'name': 'Surgical', 'description': 'Surgical instruments and supplies'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category = Category.objects.create(**cat_data)
            categories[category.name] = category
            self.stdout.write(f'📂 Created category: {category.name}')
        
        # Create suppliers
        suppliers_data = [
            {
                'name': 'MedSupply Co.',
                'contact_person': 'John Smith',
                'email': 'orders@medsupply.com',
                'phone': '+1-555-0123',
                'address': '123 Medical Ave, Healthcare City, HC 12345'
            },
            {
                'name': 'PharmaCorp Ltd.',
                'contact_person': 'Sarah Johnson',
                'email': 'supply@pharmacorp.com',
                'phone': '+1-555-0456',
                'address': '456 Pharma Street, Medicine Town, MT 67890'
            },
            {
                'name': 'EquipMed Solutions',
                'contact_person': 'Dr. Michael Brown',
                'email': 'sales@equipmed.com',
                'phone': '+1-555-0789',
                'address': '789 Equipment Blvd, Device City, DC 13579'
            },
            {
                'name': 'LabTech Supplies',
                'contact_person': 'Lisa Davis',
                'email': 'info@labtech.com',
                'phone': '+1-555-0321',
                'address': '321 Laboratory Lane, Test Valley, TV 24680'
            }
        ]
        
        suppliers = {}
        for sup_data in suppliers_data:
            supplier = Supplier.objects.create(**sup_data)
            suppliers[supplier.name] = supplier
            self.stdout.write(f'🏢 Created supplier: {supplier.name}')
        
        # Create practical medical items
        items_data = [
            # Medications
            {
                'name': 'Paracetamol 500mg Tablets',
                'description': 'Pain relief and fever reducer',
                'category': 'Medications',
                'supplier': 'PharmaCorp Ltd.',
                'unit': 'tablets',
                'price_per_unit': Decimal('0.15'),
                'quantity_in_stock': 2500,
                'minimum_quantity': 500,
                'location': 'Pharmacy - Shelf A1',
                'expiry_date': date.today() + timedelta(days=730)
            },
            {
                'name': 'Amoxicillin 250mg Capsules',
                'description': 'Antibiotic for bacterial infections',
                'category': 'Medications',
                'supplier': 'PharmaCorp Ltd.',
                'unit': 'capsules',
                'price_per_unit': Decimal('0.85'),
                'quantity_in_stock': 800,
                'minimum_quantity': 200,
                'location': 'Pharmacy - Shelf A2',
                'expiry_date': date.today() + timedelta(days=365)
            },
            {
                'name': 'Insulin (Rapid Acting)',
                'description': 'Fast-acting insulin for diabetes',
                'category': 'Medications',
                'supplier': 'PharmaCorp Ltd.',
                'unit': 'vials',
                'price_per_unit': Decimal('45.00'),
                'quantity_in_stock': 25,
                'minimum_quantity': 10,
                'location': 'Pharmacy - Refrigerator',
                'expiry_date': date.today() + timedelta(days=180)
            },
            {
                'name': 'Ibuprofen 400mg Tablets',
                'description': 'Anti-inflammatory pain reliever',
                'category': 'Medications',
                'supplier': 'PharmaCorp Ltd.',
                'unit': 'tablets',
                'price_per_unit': Decimal('0.25'),
                'quantity_in_stock': 1200,
                'minimum_quantity': 300,
                'location': 'Pharmacy - Shelf A1',
                'expiry_date': date.today() + timedelta(days=900)
            },
            
            # Medical Supplies
            {
                'name': 'Disposable Syringes 5ml',
                'description': 'Sterile disposable syringes',
                'category': 'Medical Supplies',
                'supplier': 'MedSupply Co.',
                'unit': 'pieces',
                'price_per_unit': Decimal('0.35'),
                'quantity_in_stock': 5000,
                'minimum_quantity': 1000,
                'location': 'Supply Room - Bin 1',
                'expiry_date': date.today() + timedelta(days=1095)
            },
            {
                'name': 'Surgical Gloves (Latex-Free)',
                'description': 'Sterile examination gloves',
                'category': 'Medical Supplies',
                'supplier': 'MedSupply Co.',
                'unit': 'pairs',
                'price_per_unit': Decimal('0.12'),
                'quantity_in_stock': 8000,
                'minimum_quantity': 2000,
                'location': 'Supply Room - Bin 2',
                'expiry_date': date.today() + timedelta(days=1460)
            },
            {
                'name': 'Gauze Pads 4x4 inch',
                'description': 'Sterile gauze pads for wound care',
                'category': 'Medical Supplies',
                'supplier': 'MedSupply Co.',
                'unit': 'pieces',
                'price_per_unit': Decimal('0.08'),
                'quantity_in_stock': 3000,
                'minimum_quantity': 500,
                'location': 'Supply Room - Bin 3',
                'expiry_date': date.today() + timedelta(days=1825)
            },
            {
                'name': 'Medical Face Masks',
                'description': 'Disposable surgical face masks',
                'category': 'Medical Supplies',
                'supplier': 'MedSupply Co.',
                'unit': 'pieces',
                'price_per_unit': Decimal('0.05'),
                'quantity_in_stock': 15000,
                'minimum_quantity': 5000,
                'location': 'Supply Room - Bin 4',
                'expiry_date': None
            },
            {
                'name': 'Alcohol Swabs',
                'description': '70% isopropyl alcohol prep pads',
                'category': 'Medical Supplies',
                'supplier': 'MedSupply Co.',
                'unit': 'pieces',
                'price_per_unit': Decimal('0.03'),
                'quantity_in_stock': 10000,
                'minimum_quantity': 2000,
                'location': 'Supply Room - Bin 5',
                'expiry_date': date.today() + timedelta(days=1095)
            },
            
            # Equipment
            {
                'name': 'Digital Thermometer',
                'description': 'Electronic digital thermometer',
                'category': 'Equipment',
                'supplier': 'EquipMed Solutions',
                'unit': 'pieces',
                'price_per_unit': Decimal('25.00'),
                'quantity_in_stock': 50,
                'minimum_quantity': 10,
                'location': 'Equipment Room - Shelf E1',
                'expiry_date': None
            },
            {
                'name': 'Blood Pressure Monitor',
                'description': 'Automatic digital BP monitor',
                'category': 'Equipment',
                'supplier': 'EquipMed Solutions',
                'unit': 'pieces',
                'price_per_unit': Decimal('85.00'),
                'quantity_in_stock': 15,
                'minimum_quantity': 5,
                'location': 'Equipment Room - Shelf E2',
                'expiry_date': None
            },
            {
                'name': 'Stethoscope',
                'description': 'Professional acoustic stethoscope',
                'category': 'Equipment',
                'supplier': 'EquipMed Solutions',
                'unit': 'pieces',
                'price_per_unit': Decimal('120.00'),
                'quantity_in_stock': 25,
                'minimum_quantity': 8,
                'location': 'Equipment Room - Shelf E3',
                'expiry_date': None
            },
            
            # Laboratory
            {
                'name': 'Blood Collection Tubes',
                'description': 'Vacuum blood collection tubes',
                'category': 'Laboratory',
                'supplier': 'LabTech Supplies',
                'unit': 'pieces',
                'price_per_unit': Decimal('0.45'),
                'quantity_in_stock': 2000,
                'minimum_quantity': 500,
                'location': 'Lab - Cabinet L1',
                'expiry_date': date.today() + timedelta(days=730)
            },
            {
                'name': 'Urine Test Strips',
                'description': 'Multi-parameter urine test strips',
                'category': 'Laboratory',
                'supplier': 'LabTech Supplies',
                'unit': 'strips',
                'price_per_unit': Decimal('0.75'),
                'quantity_in_stock': 500,
                'minimum_quantity': 100,
                'location': 'Lab - Cabinet L2',
                'expiry_date': date.today() + timedelta(days=365)
            },
            {
                'name': 'Glucose Test Strips',
                'description': 'Blood glucose test strips',
                'category': 'Laboratory',
                'supplier': 'LabTech Supplies',
                'unit': 'strips',
                'price_per_unit': Decimal('1.20'),
                'quantity_in_stock': 300,
                'minimum_quantity': 50,
                'location': 'Lab - Cabinet L3',
                'expiry_date': date.today() + timedelta(days=545)
            },
            
            # Emergency
            {
                'name': 'Emergency Oxygen Tank',
                'description': 'Portable oxygen cylinder',
                'category': 'Emergency',
                'supplier': 'MedSupply Co.',
                'unit': 'tanks',
                'price_per_unit': Decimal('150.00'),
                'quantity_in_stock': 12,
                'minimum_quantity': 3,
                'location': 'Emergency Room - Cabinet ER1',
                'expiry_date': None
            },
            {
                'name': 'Epinephrine Auto-Injector',
                'description': 'Emergency epinephrine injector',
                'category': 'Emergency',
                'supplier': 'PharmaCorp Ltd.',
                'unit': 'pieces',
                'price_per_unit': Decimal('95.00'),
                'quantity_in_stock': 8,
                'minimum_quantity': 3,
                'location': 'Emergency Room - Cabinet ER2',
                'expiry_date': date.today() + timedelta(days=365)
            },
            
            # Surgical
            {
                'name': 'Surgical Scalpel Blades',
                'description': 'Disposable sterile scalpel blades',
                'category': 'Surgical',
                'supplier': 'MedSupply Co.',
                'unit': 'pieces',
                'price_per_unit': Decimal('0.85'),
                'quantity_in_stock': 200,
                'minimum_quantity': 50,
                'location': 'OR - Cabinet S1',
                'expiry_date': date.today() + timedelta(days=1825)
            },
            {
                'name': 'Suture Thread (Silk)',
                'description': 'Non-absorbable silk sutures',
                'category': 'Surgical',
                'supplier': 'MedSupply Co.',
                'unit': 'packages',
                'price_per_unit': Decimal('12.50'),
                'quantity_in_stock': 150,
                'minimum_quantity': 30,
                'location': 'OR - Cabinet S2',
                'expiry_date': date.today() + timedelta(days=1460)
            }
        ]
        
        # Create items with some having low stock for demonstration
        low_stock_items = ['Insulin (Rapid Acting)', 'Epinephrine Auto-Injector', 'Glucose Test Strips']
        out_of_stock_items = ['Emergency Oxygen Tank']
        
        created_items = []
        for item_data in items_data:
            # Adjust stock for demonstration
            if item_data['name'] in low_stock_items:
                item_data['quantity_in_stock'] = item_data['minimum_quantity'] - 2
            elif item_data['name'] in out_of_stock_items:
                item_data['quantity_in_stock'] = 0
            
            item = Item.objects.create(
                name=item_data['name'],
                description=item_data['description'],
                category=categories[item_data['category']],
                supplier=suppliers[item_data['supplier']],
                unit=item_data['unit'],
                price_per_unit=item_data['price_per_unit'],
                quantity_in_stock=item_data['quantity_in_stock'],
                minimum_quantity=item_data['minimum_quantity'],
                location=item_data['location'],
                expiry_date=item_data['expiry_date'],
                barcode=f"MED{1000 + len(created_items):04d}"
            )
            created_items.append(item)
            
            # Create some stock movements for history
            if random.choice([True, False]):
                StockMovement.objects.create(
                    item=item,
                    movement_type='IN',
                    quantity=random.randint(50, 500),
                    reference=f'PO-{random.randint(1000, 9999)}',
                    notes='Initial stock purchase'
                )
        
        # Summary
        from django.db import models
        total_items = Item.objects.count()
        low_stock_count = Item.objects.filter(quantity_in_stock__lte=models.F('minimum_quantity')).count()
        out_of_stock_count = Item.objects.filter(quantity_in_stock=0).count()
        total_value = sum(item.quantity_in_stock * item.price_per_unit for item in Item.objects.all())
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 INVENTORY POPULATED SUCCESSFULLY!\n'
                f'====================================\n'
                f'📦 Total Items: {total_items}\n'
                f'⚠️  Low Stock Items: {low_stock_count}\n'
                f'❌ Out of Stock Items: {out_of_stock_count}\n'
                f'💰 Total Inventory Value: ${total_value:,.2f}\n'
                f'📂 Categories: {Category.objects.count()}\n'
                f'🏢 Suppliers: {Supplier.objects.count()}\n\n'
                f'✅ Your medical inventory is now ready for use!\n'
            )
        )
