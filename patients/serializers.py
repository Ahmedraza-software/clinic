from rest_framework import serializers
from .models import Patient, PatientDocument
from accounts.serializers import UserSerializer

class PatientDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDocument
        fields = '__all__'
        read_only_fields = ('patient', 'uploaded_at')

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    documents = PatientDocumentSerializer(many=True, read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Patient
        fields = '__all__'
        depth = 1
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        
        # Create user first
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            
            # Create patient
            patient = Patient.objects.create(user=user, **validated_data)
            return patient
        else:
            raise serializers.ValidationError(user_serializer.errors)

class PatientListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email')
    
    class Meta:
        model = Patient
        fields = ('id', 'full_name', 'email', 'date_of_birth', 'blood_group', 'is_active')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
