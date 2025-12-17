from rest_framework import serializers
from .models import Appointment, Prescription
from doctors.serializers import DoctorListSerializer
from patients.serializers import PatientListSerializer

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class AppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorListSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=DoctorListSerializer.Meta.model.objects.all(),
        source='doctor',
        write_only=True
    )
    patient = PatientListSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=PatientListSerializer.Meta.model.objects.all(),
        source='patient',
        write_only=True
    )
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_id', 'patient', 'patient_id',
            'appointment_type', 'status', 'appointment_date', 'start_time',
            'end_time', 'reason', 'symptoms', 'notes', 'is_paid',
            'payment_amount', 'payment_method', 'created_at', 'updated_at',
            'prescriptions'
        ]
        read_only_fields = ('created_at', 'updated_at')
    
    def validate(self, data):
        # Add any custom validation here
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError({"end_time": "End time must be after start time"})
        return data

class AppointmentListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor_name', 'patient_name', 'appointment_type',
            'status', 'appointment_date', 'start_time', 'end_time', 'is_paid'
        ]
    
    def get_doctor_name(self, obj):
        return f"{obj.doctor.user.first_name} {obj.doctor.user.last_name}"
    
    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}"
