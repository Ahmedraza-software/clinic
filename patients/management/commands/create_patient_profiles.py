from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from patients.models import Patient
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Create Patient records for users who don\'t have them'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get users who don't have a patient profile
        users_without_patients = User.objects.filter(patient_profile__isnull=True)
        
        if not users_without_patients.exists():
            self.stdout.write(self.style.SUCCESS('All users already have patient profiles'))
            return
            
        self.stdout.write(f'Creating patient profiles for {users_without_patients.count()} users...')
        
        # Sample data for patient profiles
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        
        for user in users_without_patients:
            # Skip if user already has a patient profile
            if hasattr(user, 'patient_profile'):
                continue
                
            # Create a patient profile with some default/sample data
            Patient.objects.create(
                user=user,
                date_of_birth=date.today() - timedelta(days=random.randint(18*365, 80*365)),
                gender=random.choice(['M', 'F', 'O']),
                blood_group=random.choice(blood_groups),
                emergency_contact_name=f"Emergency Contact for {user.get_full_name()}",
                emergency_contact_phone=f"+1{random.randint(2000000000, 9999999999)}",
                emergency_contact_relation=random.choice(['Spouse', 'Parent', 'Sibling', 'Friend']),
                allergies="None",
                current_medications="None",
                past_medical_history="None",
                family_medical_history="None",
                occupation="Not specified",
                marital_status=random.choice(['Single', 'Married', 'Divorced', 'Widowed']),
                is_active=True
            )
            self.stdout.write(f'Created patient profile for {user.email}')
            
        self.stdout.write(self.style.SUCCESS('Successfully created patient profiles'))
