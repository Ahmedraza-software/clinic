from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import Surgery, OperationTheater

@login_required
def ot_dashboard(request):
    """OT Management Dashboard"""
    # Get today's date
    today = timezone.now().date()
    
    # Get counts for the dashboard
    operation_theaters = OperationTheater.objects.annotate(
        today_surgery_count=Count(
            'surgery', 
            filter=Q(surgery__scheduled_date=today),
            distinct=True
        )
    ).prefetch_related('surgery_set')
    
    total_ots = operation_theaters.count()
    available_ots = operation_theaters.filter(is_available=True).count()
    
    # Get today's surgeries
    today_surgeries = Surgery.objects.filter(
        scheduled_date=today
    ).select_related('patient__user', 'surgeon__user', 'operation_theater')
    
    # Get upcoming surgeries (next 7 days)
    upcoming_surgeries = Surgery.objects.filter(
        scheduled_date__gt=today,
        scheduled_date__lte=today + timedelta(days=7)
    ).select_related('patient__user', 'surgeon__user', 'operation_theater')
    
    context = {
        'total_ots': total_ots,
        'available_ots': available_ots,
        'today_surgeries': today_surgeries,
        'upcoming_surgeries': upcoming_surgeries,
        'operation_theaters': operation_theaters,
        'today': today,
    }
    
    return render(request, 'operation_theater/ot_dashboard.html', context)
