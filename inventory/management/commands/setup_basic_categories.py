from django.core.management.base import BaseCommand
from inventory.models import Category


class Command(BaseCommand):
    help = 'Create basic inventory categories for admin to use'

    def handle(self, *args, **options):
        # Basic categories that most medical facilities would need
        basic_categories = [
            {
                'name': 'Medications',
                'description': 'Pharmaceutical drugs and medicines'
            },
            {
                'name': 'Medical Supplies',
                'description': 'General medical supplies and consumables'
            },
            {
                'name': 'Equipment',
                'description': 'Medical equipment and devices'
            },
            {
                'name': 'Laboratory',
                'description': 'Laboratory supplies and testing materials'
            },
            {
                'name': 'Emergency',
                'description': 'Emergency medical supplies'
            },
            {
                'name': 'Office Supplies',
                'description': 'Administrative and office supplies'
            }
        ]

        created_count = 0
        for category_data in basic_categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Setup complete. {created_count} new categories created.'
            )
        )
