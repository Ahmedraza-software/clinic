from django.core.management.base import BaseCommand
from appointments.models import Appointment
from patients.models import PatientPayment
from decimal import Decimal
from datetime import date


class Command(BaseCommand):
    help = 'Test automatic financial updates when appointment is completed'

    def handle(self, *args, **options):
        # Find an appointment that's not completed yet
        pending_appointment = Appointment.objects.filter(
            status__in=['scheduled', 'confirmed', 'in_progress']
        ).first()
        
        if not pending_appointment:
            self.stdout.write(
                self.style.ERROR('No pending appointments found to test with.')
            )
            return
        
        # Create a payment for this appointment (use appointment date)
        payment = PatientPayment.objects.create(
            patient=pending_appointment.patient,
            amount=Decimal('200.00'),
            payment_type='consultation_fee',
            payment_method='cash',
            payment_date=pending_appointment.appointment_date,
            notes=f'Test payment for appointment completion - {pending_appointment.id}'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created test payment: ${payment.amount} for {payment.patient}'
            )
        )
        
        # Get financial data before completion
        from patients.models import DoctorPayment
        current_month = date.today().replace(day=1)
        
        doctor_payment_before = DoctorPayment.objects.filter(
            doctor=pending_appointment.doctor,
            payment_period=current_month
        ).first()
        
        revenue_before = doctor_payment_before.revenue_generated if doctor_payment_before else Decimal('0')
        
        self.stdout.write(
            f'Doctor revenue before completion: ${revenue_before}'
        )
        
        # Complete the appointment
        pending_appointment.status = 'completed'
        pending_appointment.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed appointment: {pending_appointment.id}'
            )
        )
        
        # Check financial data after completion
        doctor_payment_after = DoctorPayment.objects.filter(
            doctor=pending_appointment.doctor,
            payment_period=current_month
        ).first()
        
        revenue_after = doctor_payment_after.revenue_generated if doctor_payment_after else Decimal('0')
        
        self.stdout.write(
            f'Doctor revenue after completion: ${revenue_after}'
        )
        
        if revenue_after > revenue_before:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Financial update successful! Revenue increased by ${revenue_after - revenue_before}'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Financial update failed - no revenue increase detected'
                )
            )
