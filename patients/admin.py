from django.contrib import admin
from .models import Patient, PatientDocument

class PatientDocumentInline(admin.TabularInline):
    model = PatientDocument
    extra = 1
    fields = ('document_type', 'title', 'file', 'description')
    readonly_fields = ('uploaded_at',)

class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email', 'get_phone', 'blood_group', 'is_active')
    list_filter = ('blood_group', 'gender', 'is_active')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    inlines = [PatientDocumentInline]
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Phone'
    get_phone.admin_order_field = 'user__phone'

class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'patient', 'document_type', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'patient__user__email', 'patient__user__first_name', 'patient__user__last_name')
    readonly_fields = ('uploaded_at',)

admin.site.register(Patient, PatientAdmin)
admin.site.register(PatientDocument, PatientDocumentAdmin)
