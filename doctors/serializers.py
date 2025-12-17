from rest_framework import serializers
from .models import Specialization, Doctor, DoctorSchedule
from accounts.serializers import UserSerializer

class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = '__all__'

class DoctorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = '__all__'
        read_only_fields = ('doctor',)

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    specializations = SpecializationSerializer(many=True)
    schedules = DoctorScheduleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Doctor
        fields = '__all__'
        depth = 1
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        specializations_data = validated_data.pop('specializations')
        
        # Create user first
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            
            # Create doctor
            doctor = Doctor.objects.create(user=user, **validated_data)
            
            # Add specializations
            for spec in specializations_data:
                specialization, _ = Specialization.objects.get_or_create(**spec)
                doctor.specializations.add(specialization)
                
            return doctor
        else:
            raise serializers.ValidationError(user_serializer.errors)

class DoctorListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    specializations = SpecializationSerializer(many=True)
    
    class Meta:
        model = Doctor
        fields = ('id', 'full_name', 'specializations', 'experience', 'consultation_fee', 'is_available')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
