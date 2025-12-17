from django.core.management.base import BaseCommand
from inventory.models import Supplier


class Command(BaseCommand):
    help = 'Create basic suppliers for admin to use'

    def handle(self, *args, **options):
        # Basic suppliers that most medical facilities might work with
        basic_suppliers = [
            {
                'name': 'Local Medical Supply Co.',
                'contact_person': 'Sales Department',
                'email': 'orders@localmedicalsupply.com',
                'phone': '+1-555-0123',
                'address': 'Enter supplier address here'
            },
            {
                'name': 'Pharmaceutical Distributor',
                'contact_person': 'Account Manager',
                'email': 'sales@pharmadist.com',
                'phone': '+1-555-0124',
                'address': 'Enter supplier address here'
            },
            {
                'name': 'Medical Equipment Supplier',
                'contact_person': 'Customer Service',
                'email': 'info@medequipsupply.com',
                'phone': '+1-555-0125',
                'address': 'Enter supplier address here'
            }
        ]

        created_count = 0
        for supplier_data in basic_suppliers:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults={
                    'contact_person': supplier_data['contact_person'],
                    'email': supplier_data['email'],
                    'phone': supplier_data['phone'],
                    'address': supplier_data['address']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created supplier: {supplier.name}')
            else:
                self.stdout.write(f'Supplier already exists: {supplier.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Setup complete. {created_count} new suppliers created.'
            )
        )
