from django.core.management.base import BaseCommand
from patients.models import ExpenseCategory


class Command(BaseCommand):
    help = 'Create default expense categories'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Office Supplies', 'color': 'blue'},
            {'name': 'Utilities', 'color': 'green'},
            {'name': 'Salaries', 'color': 'purple'},
            {'name': 'Rent', 'color': 'red'},
            {'name': 'Marketing', 'color': 'yellow'},
            {'name': 'Travel', 'color': 'indigo'},
            {'name': 'Medical Equipment', 'color': 'pink'},
            {'name': 'Insurance', 'color': 'gray'},
            {'name': 'Other', 'color': 'blue'},
        ]

        for category_data in categories:
            category, created = ExpenseCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'color': category_data['color'],
                    'description': f'{category_data["name"]} related expenses'
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created expense categories')
        )
