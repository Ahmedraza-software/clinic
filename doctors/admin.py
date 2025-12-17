from django.contrib import admin
from .models import Specialization, Doctor, DoctorSchedule

class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 1
    fields = ('day_of_week', 'start_time', 'end_time', 'is_working_day')

class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'get_specializations', 'is_available')
    list_filter = ('is_available', 'specialization')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'license_number')
    inlines = [DoctorScheduleInline]
    filter_horizontal = ('specialization',)
    
    def get_specializations(self, obj):
        return ", ".join([s.name for s in obj.specialization.all()])
    get_specializations.short_description = 'Specializations'

class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_working_day')
    list_filter = ('day_of_week', 'is_working_day', 'doctor')
    search_fields = ('doctor__user__email', 'doctor__user__first_name', 'doctor__user__last_name')

admin.site.register(Specialization, SpecializationAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(DoctorSchedule, DoctorScheduleAdmin)
