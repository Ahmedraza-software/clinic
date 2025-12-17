from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, time, date, timedelta

from .models import Surgery, SurgeryType, OperationTheater, SurgeryTeam, SurgeryConsumable
from .forms import SurgeryForm, SurgeryTeamForm, SurgeryConsumableForm, SurgeryStatusForm
from patients.models import Patient
from doctors.models import Doctor

# Helper function to check if user is staff/doctor
def is_staff_or_doctor(user):
    return user.is_authenticated and (user.is_staff or hasattr(user, 'doctor'))

# Dashboard View
@login_required
@user_passes_test(is_staff_or_doctor)
def dashboard(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get counts for stats cards
    scheduled_today = Surgery.objects.filter(
        scheduled_date=today,
        status='scheduled'
    ).count()
    
    completed_today = Surgery.objects.filter(
        scheduled_date=today, 
        status='completed'
    ).count()
    
    scheduled_this_week = Surgery.objects.filter(
        scheduled_date__range=[start_of_week, end_of_week],
        status='scheduled'
    ).count()
    
    postponed = Surgery.objects.filter(status='postponed').count()
    
    # Today's schedule
    today_schedule = Surgery.objects.filter(
        scheduled_date=today
    ).order_by('start_time')
    
    # Upcoming surgeries (next 7 days)
    upcoming_surgeries = Surgery.objects.filter(
        scheduled_date__gt=today,
        scheduled_date__lte=today + timedelta(days=7)
    ).order_by('scheduled_date', 'start_time')[:5]
    
    # Recent consumables usage
    recent_consumables = SurgeryConsumable.objects.select_related('surgery').order_by('-used_at')[:5]
    
    # Get OT utilization for the current week (simplified example)
    ot_utilization = []
    theaters = OperationTheater.objects.all()
    for ot in theaters:
        surgery_count = Surgery.objects.filter(
            operation_theater=ot,
            scheduled_date__range=[start_of_week, end_of_week]
        ).count()
        ot_utilization.append({
            'name': ot.name,
            'surgery_count': surgery_count
        })
    
    # Prepare data for chart
    ot_names = json.dumps([ot['name'] for ot in ot_utilization])
    scheduled_data = json.dumps([ot['surgery_count'] for ot in ot_utilization])
    completed_data = json.dumps([0 for _ in ot_utilization])  # Placeholder data
    available_data = json.dumps([10 for _ in ot_utilization])  # Placeholder data
    
    context = {
        'scheduled_today': scheduled_today,
        'completed_today': completed_today,
        'scheduled_this_week': scheduled_this_week,
        'postponed': postponed,
        'today_schedule': today_schedule,
        'upcoming_surgeries': upcoming_surgeries,
        'recent_consumables': recent_consumables,
        'ot_utilization': ot_utilization,
        'ot_names': ot_names,
        'scheduled_data': scheduled_data,
        'completed_data': completed_data,
        'available_data': available_data,
    }
    
    return render(request, 'operation_theater/dashboard.html', context)

# Surgery List View
class SurgeryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Surgery
    template_name = 'operation_theater/surgery_list.html'
    context_object_name = 'surgeries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Surgery.objects.select_related(
            'patient__user', 'surgeon__user', 'surgery_type', 'operation_theater'
        ).order_by('-scheduled_date', '-start_time')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(patient__user__first_name__icontains=search_query) |
                Q(patient__user__last_name__icontains=search_query) |
                Q(surgeon__user__first_name__icontains=search_query) |
                Q(surgeon__user__last_name__icontains=search_query) |
                Q(surgery_type__name__icontains=search_query) |
                Q(operation_theater__name__icontains=search_query)
            )
            
        return queryset
    
    def test_func(self):
        return is_staff_or_doctor(self.request.user)

# Surgery Detail View
class SurgeryDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Surgery
    template_name = 'operation_theater/surgery_detail.html'
    context_object_name = 'surgery'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_form'] = SurgeryTeamForm(surgery=self.object)
        context['consumable_form'] = SurgeryConsumableForm()
        context['status_form'] = SurgeryStatusForm(instance=self.object)
        
        # Add available doctors for team member selection
        context['available_doctors'] = Doctor.objects.all().order_by('user__first_name', 'user__last_name')
        
        return context
    
    def test_func(self):
        return is_staff_or_doctor(self.request.user)

# Create Surgery View
class SurgeryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Surgery
    form_class = SurgeryForm
    template_name = 'operation_theater/surgery_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        print("Form is being submitted")
        print("Form data:", form.cleaned_data)
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Surgery scheduled successfully!')
            print("Surgery created successfully with ID:", self.object.pk)
            return response
        except Exception as e:
            print("Error saving surgery:", e)
            messages.error(self.request, f'Error scheduling surgery: {str(e)}')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('operation_theater:dashboard')
    
    def test_func(self):
        return is_staff_or_doctor(self.request.user)

# Update Surgery View
class SurgeryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Surgery
    form_class = SurgeryForm
    template_name = 'operation_theater/surgery_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Surgery updated successfully.')
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('operation_theater:surgery_detail', kwargs={'pk': self.object.pk})
    
    def test_func(self):
        return is_staff_or_doctor(self.request.user)

# Delete Surgery View
class SurgeryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Surgery
    template_name = 'operation_theater/surgery_confirm_delete.html'
    success_url = reverse_lazy('operation_theater:surgery_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Surgery has been deleted.')
        return super().delete(request, *args, **kwargs)
    
    def test_func(self):
        return self.request.user.is_staff

# Add Team Member View
@login_required
@user_passes_test(is_staff_or_doctor)
def add_team_member(request, surgery_id):
    surgery = get_object_or_404(Surgery, id=surgery_id)
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        if doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                
                # Check if doctor is already in the team
                if SurgeryTeam.objects.filter(surgery=surgery, doctor=doctor).exists():
                    messages.warning(request, f'Dr. {doctor.user.get_full_name()} already exists in team.')
                else:
                    # Create team member with default role
                    team_member = SurgeryTeam.objects.create(
                        surgery=surgery,
                        doctor=doctor,
                        role='surgeon',  # Default role
                        is_primary=False
                    )
                    messages.success(request, f'Dr. {doctor.user.get_full_name()} added to team.')
                    
            except Doctor.DoesNotExist:
                messages.error(request, 'Selected doctor not found.')
            except Exception as e:
                messages.error(request, f'Error adding team member: {str(e)}')
        else:
            messages.error(request, 'Please select a doctor.')
    
    return redirect('operation_theater:surgery_detail', pk=surgery_id)

# Remove Team Member View
@login_required
@user_passes_test(is_staff_or_doctor)
def remove_team_member(request, team_member_id):
    team_member = get_object_or_404(SurgeryTeam, id=team_member_id)
    surgery_id = team_member.surgery.id
    team_member.delete()
    messages.success(request, 'Team member removed successfully.')
    return redirect('operation_theater:surgery_detail', pk=surgery_id)

# Add Consumable View
@login_required
@user_passes_test(is_staff_or_doctor)
def add_consumable(request, surgery_id):
    surgery = get_object_or_404(Surgery, id=surgery_id)
    
    if request.method == 'POST':
        form = SurgeryConsumableForm(request.POST)
        if form.is_valid():
            consumable = form.save(commit=False)
            consumable.surgery = surgery
            consumable.recorded_by = request.user
            consumable.save()
            messages.success(request, 'Consumable added successfully.')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('operation_theater:surgery_detail', pk=surgery_id)

# Update Surgery Status
@login_required
@user_passes_test(is_staff_or_doctor)
def update_surgery_status(request, surgery_id):
    surgery = get_object_or_404(Surgery, id=surgery_id)
    
    if request.method == 'POST':
        form = SurgeryStatusForm(request.POST, instance=surgery)
        if form.is_valid():
            form.save()
            messages.success(request, f'Surgery status updated to {surgery.get_status_display()}.')
    
    return redirect('operation_theater:surgery_detail', pk=surgery_id)

# Update Surgery Notes
@login_required
@user_passes_test(is_staff_or_doctor)
def update_surgery_notes(request, surgery_id):
    surgery = get_object_or_404(Surgery, id=surgery_id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        surgery.notes = notes
        surgery.save()
        messages.success(request, 'Surgery notes updated successfully.')
    
    return redirect('operation_theater:surgery_detail', pk=surgery_id)

# Get Available Time Slots (AJAX)
@login_required
@require_http_methods(['GET'])
def get_available_time_slots(request):
    date_str = request.GET.get('date')
    theater_id = request.GET.get('theater_id')
    surgery_id = request.GET.get('surgery_id')
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get all time slots (30-minute intervals from 8 AM to 8 PM)
    time_slots = []
    start_time = time(8, 0)
    end_time = time(20, 0)
    
    current = datetime.combine(selected_date, start_time)
    end = datetime.combine(selected_date, end_time)
    
    while current <= end - timedelta(minutes=30):
        time_slots.append({
            'start': current.time().strftime('%H:%M'),
            'end': (current + timedelta(minutes=30)).time().strftime('%H:%M'),
            'available': True
        })
        current += timedelta(minutes=30)
    
    # Mark unavailable time slots
    if theater_id:
        # Get all surgeries for the selected date and theater
        surgeries = Surgery.objects.filter(
            operation_theater_id=theater_id,
            scheduled_date=selected_date,
            status__in=['scheduled', 'in_progress']
        )
        
        # Exclude current surgery when editing
        if surgery_id:
            surgeries = surgeries.exclude(id=surgery_id)
        
        # Mark unavailable time slots
        for slot in time_slots:
            slot_start = datetime.strptime(slot['start'], '%H:%M').time()
            slot_end = datetime.strptime(slot['end'], '%H:%M').time()
            
            for surgery in surgeries:
                if (surgery.start_time < slot_end and surgery.end_time > slot_start):
                    slot['available'] = False
                    break
    
    return JsonResponse({'time_slots': time_slots})

# Operation Theater Calendar View
@login_required
@user_passes_test(is_staff_or_doctor)
def ot_calendar(request):
    return render(request, 'operation_theater/ot_calendar.html')

# Get Calendar Events (AJAX)
@login_required
@require_http_methods(['GET'])
def get_calendar_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get all surgeries in the date range
    surgeries = Surgery.objects.filter(
        scheduled_date__range=[start_date, end_date]
    ).select_related('patient__user', 'surgeon__user', 'operation_theater')
    
    # Format events for FullCalendar
    events = []
    for surgery in surgeries:
        # Set color based on status
        if surgery.status == 'completed':
            color = '#10B981'  # Green
        elif surgery.status == 'cancelled':
            color = '#EF4444'  # Red
        elif surgery.status == 'postponed':
            color = '#F59E0B'  # Yellow
        elif surgery.status == 'in_progress':
            color = '#3B82F6'  # Blue
        else:  # scheduled
            color = '#8B5CF6'  # Purple
        
        events.append({
            'id': surgery.id,
            'title': f"{surgery.patient.user.get_full_name()} - {surgery.surgery_type.name}",
            'start': f"{surgery.scheduled_date}T{surgery.start_time}",
            'end': f"{surgery.scheduled_date}T{surgery.end_time}",
            'color': color,
            'extendedProps': {
                'theater': surgery.operation_theater.name,
                'surgeon': surgery.surgeon.user.get_full_name(),
                'status': surgery.get_status_display(),
                'notes': surgery.notes or ''
            }
        })
    
    return JsonResponse(events, safe=False)

# Operation Theater List View
class OperationTheaterListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = OperationTheater
    template_name = 'operation_theater/ot_list.html'
    context_object_name = 'operation_theaters'
    
    def test_func(self):
        return self.request.user.is_staff

# Operation Theater Create View
class OperationTheaterCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = OperationTheater
    fields = ['name', 'location', 'is_available', 'description', 'supervising_doctors']
    template_name = 'operation_theater/ot_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Operation Theater created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('operation_theater:ot_list')
    
    def test_func(self):
        return self.request.user.is_staff

# Operation Theater Update View
class OperationTheaterUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = OperationTheater
    fields = ['name', 'location', 'is_available', 'description', 'supervising_doctors']
    template_name = 'operation_theater/ot_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Operation Theater updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('operation_theater:ot_list')
    
    def test_func(self):
        return self.request.user.is_staff

# Operation Theater Delete View
class OperationTheaterDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = OperationTheater
    template_name = 'operation_theater/ot_confirm_delete.html'
    success_url = reverse_lazy('operation_theater:ot_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Operation Theater has been deleted.')
        return super().delete(request, *args, **kwargs)
    
    def test_func(self):
        return self.request.user.is_staff

# Surgery Type List View
class SurgeryTypeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SurgeryType
    template_name = 'operation_theater/surgery_type_list.html'
    context_object_name = 'surgery_types'
    
    def test_func(self):
        return self.request.user.is_staff

# Surgery Type Create/Update View
class SurgeryTypeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SurgeryType
    fields = ['name', 'description', 'duration', 'category', 'preparation_instructions', 'post_op_instructions']
    template_name = 'operation_theater/surgery_type_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Surgery Type created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('operation_theater:surgery_type_list')
    
    def test_func(self):
        return self.request.user.is_staff


class SurgeryTypeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SurgeryType
    fields = ['name', 'description', 'duration', 'category', 'preparation_instructions', 'post_op_instructions']
    template_name = 'operation_theater/surgery_type_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Surgery Type updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('operation_theater:surgery_type_list')
    
    def test_func(self):
        return self.request.user.is_staff
