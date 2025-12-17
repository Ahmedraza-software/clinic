from django.contrib import admin
from .models import (
    PatientMedicalRecord, VitalSigns, DigitalFormTemplate, FilledForm,
    Equipment, EquipmentCheckout, AlertRule, Alert, ReportTemplate, GeneratedReport
)

@admin.register(PatientMedicalRecord)
class PatientMedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'blood_type', 'created_at', 'updated_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'patient__user__email')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = ('patient', 'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                   'heart_rate', 'recorded_at')
    list_filter = ('recorded_at',)
    search_fields = ('patient__user__first_name', 'patient__user__last_name')
    date_hierarchy = 'recorded_at'

@admin.register(DigitalFormTemplate)
class DigitalFormTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'form_type', 'is_active', 'created_at')
    list_filter = ('form_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(FilledForm)
class FilledFormAdmin(admin.ModelAdmin):
    list_display = ('template', 'patient', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'template__form_type', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'template__name')
    readonly_fields = ('created_at', 'updated_at')

class EquipmentCheckoutInline(admin.StackedInline):
    model = EquipmentCheckout
    extra = 0
    readonly_fields = ('checkout_time', 'return_time')

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'status', 'location', 'last_maintenance')
    list_filter = ('equipment_type', 'status', 'last_maintenance')
    search_fields = ('name', 'model_number', 'serial_number', 'barcode', 'rfid_tag')
    inlines = [EquipmentCheckoutInline]

@admin.register(EquipmentCheckout)
class EquipmentCheckoutAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'patient', 'checked_out_by', 'checkout_time', 'return_time', 'is_overdue')
    list_filter = ('checkout_time', 'return_time')
    search_fields = ('equipment__name', 'patient__user__first_name', 'patient__user__last_name')
    readonly_fields = ('is_overdue',)

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'alert_type', 'severity', 'is_active')
    list_filter = ('alert_type', 'severity', 'is_active')
    search_fields = ('name', 'message_template')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('rule', 'patient', 'is_acknowledged', 'created_at')
    list_filter = ('is_acknowledged', 'rule__alert_type', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'message')
    readonly_fields = ('created_at',)

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'is_active')
    list_filter = ('report_type', 'is_active')
    search_fields = ('name', 'description')

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('template', 'patient', 'created_at')
    list_filter = ('template__report_type', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'template__name')
    readonly_fields = ('created_at',)
