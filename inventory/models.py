from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='items')
    unit = models.CharField(max_length=50, help_text='e.g., pcs, boxes, kg, etc.')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_in_stock = models.PositiveIntegerField(default=0)
    minimum_quantity = models.PositiveIntegerField(default=5, help_text='Minimum quantity before restock alert')
    location = models.CharField(max_length=100, help_text='Storage location in the facility')
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity_in_stock} {self.unit} in stock)"

    @property
    def needs_restock(self):
        return self.quantity_in_stock <= self.minimum_quantity

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
        ('RETURN', 'Return to Supplier'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(help_text='Positive for stock in, negative for stock out')
    reference = models.CharField(max_length=100, blank=True, null=True, help_text='Reference number or description')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Update item quantity when saving stock movement
        if not self.pk:  # Only on creation
            self.item.quantity_in_stock += self.quantity
            self.item.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.quantity} of {self.item.name}"
