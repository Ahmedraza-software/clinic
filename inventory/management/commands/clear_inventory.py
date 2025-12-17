from django.core.management.base import BaseCommand
from inventory.models import Item, Category, Supplier, StockMovement


class Command(BaseCommand):
    help = 'Clear all inventory data (items, categories, suppliers, stock movements)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all inventory data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL inventory data. '
                    'Run with --confirm to proceed.'
                )
            )
            return

        # Delete all data in reverse order of dependencies
        self.stdout.write('Deleting stock movements...')
        stock_movements_count = StockMovement.objects.count()
        StockMovement.objects.all().delete()
        
        self.stdout.write('Deleting items...')
        items_count = Item.objects.count()
        Item.objects.all().delete()
        
        self.stdout.write('Deleting suppliers...')
        suppliers_count = Supplier.objects.count()
        Supplier.objects.all().delete()
        
        self.stdout.write('Deleting categories...')
        categories_count = Category.objects.count()
        Category.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleared inventory data:\n'
                f'- {stock_movements_count} stock movements deleted\n'
                f'- {items_count} items deleted\n'
                f'- {suppliers_count} suppliers deleted\n'
                f'- {categories_count} categories deleted'
            )
        )
