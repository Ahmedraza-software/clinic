from django.core.management.base import BaseCommand
from patients.models import Expense, ExpenseCategory
from decimal import Decimal
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Create sample expense data for testing charts'

    def handle(self, *args, **options):
        # Get or create categories
        categories = []
        category_names = ['Office Supplies', 'Utilities', 'Salaries', 'Rent', 'Marketing', 'Travel']
        
        for name in category_names:
            category, created = ExpenseCategory.objects.get_or_create(
                name=name,
                defaults={'color': 'blue'}
            )
            categories.append(category)

        # Create sample expenses for the last 12 months
        today = date.today()
        
        for i in range(365):  # Last 365 days
            expense_date = today - timedelta(days=i)
            
            # Create 0-3 random expenses per day
            num_expenses = random.randint(0, 3)
            
            for j in range(num_expenses):
                category = random.choice(categories)
                amount = Decimal(str(random.randint(50, 2000)))
                
                descriptions = {
                    'Office Supplies': ['Paper and pens', 'Printer cartridges', 'Office furniture', 'Stationery'],
                    'Utilities': ['Electricity bill', 'Water bill', 'Internet service', 'Phone service'],
                    'Salaries': ['Staff salary', 'Doctor fees', 'Nurse salary', 'Admin salary'],
                    'Rent': ['Office rent', 'Equipment lease', 'Parking rent'],
                    'Marketing': ['Advertisement', 'Website maintenance', 'Social media ads', 'Brochures'],
                    'Travel': ['Conference travel', 'Medical training', 'Business trip', 'Transportation']
                }
                
                description = random.choice(descriptions[category.name])
                payment_method = random.choice(['cash', 'credit_card', 'bank_transfer', 'check'])
                
                Expense.objects.create(
                    description=description,
                    amount=amount,
                    category=category,
                    payment_method=payment_method,
                    expense_date=expense_date,
                    is_recurring=random.choice([True, False]) if random.random() < 0.1 else False
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample expense data')
        )
