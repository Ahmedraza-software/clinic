from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F, Sum, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Item, Category, Supplier, StockMovement
from decimal import Decimal
from datetime import date, timedelta
import json


@login_required
def inventory_dashboard(request):
    """Main inventory dashboard with statistics and overview"""
    
    # Get filter parameters
    category_filter = request.GET.get('category', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset with calculated total value
    items = Item.objects.filter(is_active=True).select_related('category', 'supplier').annotate(
        total_value=F('quantity_in_stock') * F('price_per_unit')
    )
    
    # Apply filters
    if category_filter != 'all':
        items = items.filter(category__name=category_filter)
    
    if status_filter == 'low_stock':
        items = items.filter(quantity_in_stock__lte=F('minimum_quantity'))
    elif status_filter == 'out_of_stock':
        items = items.filter(quantity_in_stock=0)
    elif status_filter == 'in_stock':
        items = items.filter(quantity_in_stock__gt=F('minimum_quantity'))
    
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_items = Item.objects.filter(is_active=True).count()
    low_stock_items = Item.objects.filter(
        is_active=True,
        quantity_in_stock__lte=F('minimum_quantity')
    ).count()
    out_of_stock_items = Item.objects.filter(
        is_active=True,
        quantity_in_stock=0
    ).count()
    
    # Calculate total inventory value
    total_value = Item.objects.filter(is_active=True).aggregate(
        total=Sum(F('quantity_in_stock') * F('price_per_unit'))
    )['total'] or Decimal('0')
    
    # Top items by value
    top_items_by_value = Item.objects.filter(is_active=True).annotate(
        total_value=F('quantity_in_stock') * F('price_per_unit')
    ).order_by('-total_value')[:5]
    
    # Top items by quantity
    top_items_by_quantity = Item.objects.filter(is_active=True).order_by('-quantity_in_stock')[:5]
    
    # Items expiring soon (within 30 days)
    expiring_soon = Item.objects.filter(
        is_active=True,
        expiry_date__lte=date.today() + timedelta(days=30),
        expiry_date__gte=date.today()
    ).order_by('expiry_date')[:5]
    
    # Recent stock movements
    recent_movements = StockMovement.objects.select_related('item', 'created_by').order_by('-created_at')[:10]
    
    # Categories for filter dropdown
    categories = Category.objects.all()
    
    context = {
        'items': page_obj,
        'categories': categories,
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'total_value': total_value,
        'top_items_by_value': top_items_by_value,
        'top_items_by_quantity': top_items_by_quantity,
        'expiring_soon': expiring_soon,
        'recent_movements': recent_movements,
        'current_category': category_filter,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/dashboard.html', context)


@login_required
def add_item(request):
    """Add new inventory item"""
    if request.method == 'POST':
        try:
            item = Item.objects.create(
                name=request.POST['name'],
                description=request.POST.get('description', ''),
                category_id=request.POST['category'],
                supplier_id=request.POST.get('supplier'),
                unit=request.POST['unit'],
                price_per_unit=Decimal(request.POST['price_per_unit']),
                quantity_in_stock=int(request.POST['quantity_in_stock']),
                minimum_quantity=int(request.POST['minimum_quantity']),
                location=request.POST.get('location', ''),
                barcode=request.POST.get('barcode', ''),
                expiry_date=request.POST.get('expiry_date') or None,
            )
            
            # Create initial stock movement
            if item.quantity_in_stock > 0:
                StockMovement.objects.create(
                    item=item,
                    movement_type='IN',
                    quantity=item.quantity_in_stock,
                    reference='Initial Stock',
                    notes='Item added to inventory',
                    created_by=request.user
                )
            
            messages.success(request, f'Item "{item.name}" added successfully!')
            return redirect('inventory:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding item: {str(e)}')
    
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    
    return render(request, 'inventory/add_item.html', {
        'categories': categories,
        'suppliers': suppliers
    })


@login_required
def update_stock(request, item_id):
    """Update item stock quantity"""
    item = get_object_or_404(Item, id=item_id)
    
    # Debug: uncomment these lines if you need to debug
    # print(f"Stock update request for item {item_id}: {item.name}")
    # print(f"Request method: {request.method}")
    # print(f"POST data: {request.POST}")
    
    if request.method == 'POST':
        try:
            movement_type = request.POST['movement_type']
            quantity = int(request.POST['quantity'])
            reference = request.POST.get('reference', '')
            notes = request.POST.get('notes', '')
            
            # Validate stock out doesn't exceed current stock
            if movement_type == 'OUT' and quantity > item.quantity_in_stock:
                messages.error(request, 'Cannot remove more stock than available!')
                return redirect('inventory:dashboard')
            
            # Create stock movement
            if movement_type == 'IN':
                movement_quantity = quantity
            elif movement_type == 'OUT':
                movement_quantity = -quantity
            else:  # ADJUST
                movement_quantity = quantity - item.quantity_in_stock
            
            StockMovement.objects.create(
                item=item,
                movement_type=movement_type,
                quantity=movement_quantity,
                reference=reference,
                notes=notes,
                created_by=request.user
            )
            
            # Update item stock
            if movement_type == 'ADJUST':
                item.quantity_in_stock = quantity
            else:
                item.quantity_in_stock += movement_quantity
            item.save()
            
            messages.success(request, f'Stock updated for "{item.name}"!')
            
        except Exception as e:
            messages.error(request, f'Error updating stock: {str(e)}')
    
    return redirect('inventory:dashboard')


@login_required
def low_stock_report(request):
    """Report of items with low stock"""
    low_stock_items = Item.objects.filter(
        is_active=True,
        quantity_in_stock__lte=F('minimum_quantity')
    ).select_related('category', 'supplier').order_by('quantity_in_stock')
    
    return render(request, 'inventory/low_stock_report.html', {
        'low_stock_items': low_stock_items
    })


@login_required
def expiry_report(request):
    """Report of items expiring soon"""
    # Items expiring within 30 days
    expiring_soon = Item.objects.filter(
        is_active=True,
        expiry_date__lte=date.today() + timedelta(days=30),
        expiry_date__gte=date.today()
    ).select_related('category').order_by('expiry_date')
    
    # Expired items
    expired_items = Item.objects.filter(
        is_active=True,
        expiry_date__lt=date.today()
    ).select_related('category').order_by('expiry_date')
    
    return render(request, 'inventory/expiry_report.html', {
        'expiring_soon': expiring_soon,
        'expired_items': expired_items
    })


@login_required
def stock_movements(request, item_id):
    """View stock movement history for an item"""
    item = get_object_or_404(Item, id=item_id)
    movements = item.movements.select_related('created_by').order_by('-created_at')
    
    # Calculate total value
    item.total_value = item.quantity_in_stock * item.price_per_unit
    
    return render(request, 'inventory/stock_movements.html', {
        'item': item,
        'movements': movements
    })


@login_required
def export_inventory(request):
    """Export inventory data as JSON"""
    items = Item.objects.filter(is_active=True).select_related('category', 'supplier')
    
    data = []
    for item in items:
        data.append({
            'name': item.name,
            'category': item.category.name if item.category else '',
            'supplier': item.supplier.name if item.supplier else '',
            'unit': item.unit,
            'price_per_unit': float(item.price_per_unit),
            'quantity_in_stock': item.quantity_in_stock,
            'minimum_quantity': item.minimum_quantity,
            'location': item.location,
            'barcode': item.barcode or '',
            'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
            'total_value': float(item.quantity_in_stock * item.price_per_unit),
            'needs_restock': item.needs_restock
        })
    
    response = JsonResponse({
        'export_date': date.today().isoformat(),
        'total_items': len(data),
        'items': data
    })
    response['Content-Disposition'] = f'attachment; filename="inventory_export_{date.today()}.json"'
    
    return response
