from django.contrib import admin
from .models import Appointment, Prescription

class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1
    fields = ('medication_name', 'dosage', 'frequency', 'duration', 'duration_unit', 'is_active')

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'is_paid')
    list_filter = ('status', 'appointment_type', 'appointment_date', 'is_paid')
    search_fields = (
        'patient__user__email', 
        'patient__user__first_name', 
        'patient__user__last_name',
        'doctor__user__email',
        'doctor__user__first_name',
        'doctor__user__last_name'
    )
    inlines = [PrescriptionInline]
    date_hierarchy = 'appointment_date'
    ordering = ('-appointment_date', '-appointment_time')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient__user', 'doctor__user')

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('medication_name', 'patient', 'doctor', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'frequency', 'duration_unit')
    search_fields = (
        'medication_name',
        'patient__user__email',
        'patient__user__first_name',
        'patient__user__last_name',
        'doctor__user__email',
        'doctor__user__first_name',
        'doctor__user__last_name'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient__user', 'doctor__user')

admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
