from django.core.management.base import BaseCommand
from appointments.models import Appointment
from doctors.models import Doctor
from patients.models import Patient, PatientPayment
from datetime import date, timedelta
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Create completed appointments with associated payments for testing doctor revenue'

    def handle(self, *args, **options):
        # Get doctors and patients
        doctors = Doctor.objects.all()
        patients = Patient.objects.all()
        
        if not doctors.exists():
            self.stdout.write(
                self.style.ERROR('No doctors found. Please create doctors first.')
            )
            return
            
        if not patients.exists():
            self.stdout.write(
                self.style.ERROR('No patients found. Please create patients first.')
            )
            return

        # Create completed appointments for this month
        today = date.today()
        current_month = today.replace(day=1)
        
        appointments_created = 0
        payments_created = 0
        
        for i in range(20):  # Create 20 completed appointments
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            
            # Random date this month
            days_in_month = (today.replace(month=today.month % 12 + 1, day=1) - timedelta(days=1)).day
            random_day = random.randint(1, min(today.day, days_in_month))
            appointment_date = current_month.replace(day=random_day)
            
            # Create completed appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=f"{random.randint(9, 17):02d}:00",
                appointment_type='consultation',
                status='completed',
                reason='Regular checkup',
                notes='Appointment completed successfully'
            )
            appointments_created += 1
            
            # Create associated payment (consultation fee)
            consultation_fee = Decimal(str(random.randint(100, 500)))
            payment_date = appointment_date + timedelta(days=random.randint(0, 3))
            
            payment = PatientPayment.objects.create(
                patient=patient,
                amount=consultation_fee,
                payment_type='consultation_fee',
                payment_method='cash',
                payment_date=payment_date,
                notes=f'Consultation fee for appointment with Dr. {doctor.user.get_full_name()}'
            )
            payments_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {appointments_created} completed appointments '
                f'and {payments_created} associated payments'
            )
        )
