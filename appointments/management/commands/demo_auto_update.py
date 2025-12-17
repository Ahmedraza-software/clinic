from django.core.management.base import BaseCommand
from appointments.models import Appointment
from patients.models import PatientPayment
from decimal import Decimal
from datetime import date
import time


class Command(BaseCommand):
    help = 'Demonstrate automatic financial updates when appointments are completed'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                '\n🏥 DEMO: Automatic Financial Updates\n'
                '=====================================\n'
            )
        )
        
        # Find pending appointments
        pending_appointments = Appointment.objects.filter(
            status__in=['scheduled', 'confirmed', 'in_progress']
        )[:3]  # Get up to 3 appointments
        
        if not pending_appointments.exists():
            self.stdout.write(
                self.style.ERROR('No pending appointments found for demo.')
            )
            return
        
        self.stdout.write(
            f'Found {pending_appointments.count()} pending appointments to complete...\n'
        )
        
        for i, appointment in enumerate(pending_appointments, 1):
            self.stdout.write(
                f'📋 Step {i}: Completing appointment for {appointment.patient}'
            )
            
            # Create payment for this appointment
            payment_amount = Decimal(str(150 + (i * 50)))  # $150, $200, $250
            payment = PatientPayment.objects.create(
                patient=appointment.patient,
                amount=payment_amount,
                payment_type='consultation_fee',
                payment_method='cash',
                payment_date=appointment.appointment_date,
                notes=f'Demo payment - appointment completion #{i}'
            )
            
            self.stdout.write(f'💰 Created payment: ${payment_amount}')
            
            # Complete the appointment (this triggers automatic financial update)
            appointment.status = 'completed'
            appointment.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Appointment completed! Financial data automatically updated.\n'
                )
            )
            
            # Small delay for demonstration
            time.sleep(1)
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 DEMO COMPLETE!\n'
                '=================\n'
                '📊 The Accounts & Finance page will now show:\n'
                '   • Updated doctor revenue totals\n'
                '   • Increased completed appointment counts\n'
                '   • Real-time financial metrics\n'
                '   • Automatic refresh every 30 seconds\n\n'
                '🔄 Visit /finance/accounts/ to see the live updates!'
            )
        )
