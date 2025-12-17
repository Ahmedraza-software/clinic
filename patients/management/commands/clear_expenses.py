from django.core.management.base import BaseCommand
from patients.models import Expense


class Command(BaseCommand):
    help = 'Delete all expense records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all expenses',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING('This will delete ALL expense records. Use --confirm to proceed.')
            )
            return

        expense_count = Expense.objects.count()
        
        if expense_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No expenses found to delete.')
            )
            return

        # Delete all expenses
        Expense.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {expense_count} expense records.')
        )
