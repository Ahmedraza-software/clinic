from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from patients.models import Patient
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Add a test patient to the database'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create a new user
        user, created = User.objects.get_or_create(
            username='test.patient@example.com',
            defaults={
                'email': 'test.patient@example.com',
                'first_name': 'Test',
                'last_name': 'Patient',
                'is_active': True,
            }
        )
        
        if created:
            user.set_password('TestPass123!')
            user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created user: %s' % user.email))
        else:
            self.stdout.write(self.style.WARNING('User already exists: %s' % user.email))
        
        # Create patient profile
        patient, p_created = Patient.objects.get_or_create(
            user=user,
            defaults={
                'date_of_birth': date.today() - timedelta(days=30*365),  # ~30 years old
                'gender': 'M',
                'blood_group': 'O+',
                'address': '123 Test Street, Test City',
                'phone': '+1234567890',
            }
        )
        
        if p_created:
            self.stdout.write(self.style.SUCCESS('Successfully created patient profile for: %s' % user.get_full_name()))
        else:
            self.stdout.write(self.style.WARNING('Patient profile already exists for: %s' % user.get_full_name()))
        
        self.stdout.write(self.style.SUCCESS('Test patient added successfully!'))
