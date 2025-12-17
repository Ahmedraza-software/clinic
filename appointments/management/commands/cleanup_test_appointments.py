from django.core.management.base import BaseCommand
from appointments.models import Appointment
from patients.models import PatientPayment
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Remove test appointments and keep only 2-3 real appointments'

    def handle(self, *args, **options):
        # Get current month
        today = date.today()
        current_month = today.replace(day=1)
        
        # Delete all appointments created by the test command (completed status from this month)
        test_appointments = Appointment.objects.filter(
            appointment_date__gte=current_month,
            status='completed',
            notes='Appointment completed successfully'  # This was added by our test command
        )
        
        appointments_deleted = test_appointments.count()
        
        # Also delete associated test payments
        test_payments = PatientPayment.objects.filter(
            payment_date__gte=current_month,
            payment_type='consultation_fee',
            notes__icontains='Consultation fee for appointment with Dr.'
        )
        
        payments_deleted = test_payments.count()
        
        # Delete the test data
        test_payments.delete()
        test_appointments.delete()
        
        # Keep only 2-3 appointments - let's create a couple of realistic ones
        from doctors.models import Doctor
        from patients.models import Patient
        from decimal import Decimal
        
        doctors = Doctor.objects.all()[:2]  # Get first 2 doctors
        patients = Patient.objects.all()[:3]  # Get first 3 patients
        
        if doctors.exists() and patients.exists():
            # Create 2 completed appointments
            completed_appointments = [
                {
                    'patient': patients[0],
                    'doctor': doctors[0],
                    'date': today - timedelta(days=2),
                    'time': '10:00',
                    'type': 'consultation',
                    'status': 'completed',
                    'reason': 'Regular checkup',
                    'fee': Decimal('200.00')
                },
                {
                    'patient': patients[1], 
                    'doctor': doctors[1] if len(doctors) > 1 else doctors[0],
                    'date': today - timedelta(days=1),
                    'time': '14:00',
                    'type': 'consultation', 
                    'status': 'completed',
                    'reason': 'Follow-up consultation',
                    'fee': Decimal('150.00')
                }
            ]
            
            # Create 1 in-progress appointment
            in_progress_appointment = {
                'patient': patients[2] if len(patients) > 2 else patients[0],
                'doctor': doctors[0],
                'date': today,
                'time': '16:00',
                'type': 'consultation',
                'status': 'in_progress', 
                'reason': 'Routine examination',
                'fee': Decimal('180.00')
            }
            
            appointments_created = 0
            payments_created = 0
            
            # Create the appointments
            for apt_data in completed_appointments:
                appointment = Appointment.objects.create(
                    patient=apt_data['patient'],
                    doctor=apt_data['doctor'],
                    appointment_date=apt_data['date'],
                    appointment_time=apt_data['time'],
                    appointment_type=apt_data['type'],
                    status=apt_data['status'],
                    reason=apt_data['reason'],
                    notes=f"Real appointment - {apt_data['reason']}"
                )
                appointments_created += 1
                
                # Create payment for completed appointments
                if apt_data['status'] == 'completed':
                    PatientPayment.objects.create(
                        patient=apt_data['patient'],
                        amount=apt_data['fee'],
                        payment_type='consultation_fee',
                        payment_method='cash',
                        payment_date=apt_data['date'],
                        notes=f'Consultation fee - {apt_data["reason"]}'
                    )
                    payments_created += 1
            
            # Create in-progress appointment
            Appointment.objects.create(
                patient=in_progress_appointment['patient'],
                doctor=in_progress_appointment['doctor'],
                appointment_date=in_progress_appointment['date'],
                appointment_time=in_progress_appointment['time'],
                appointment_type=in_progress_appointment['type'],
                status=in_progress_appointment['status'],
                reason=in_progress_appointment['reason'],
                notes=f"Real appointment - {in_progress_appointment['reason']}"
            )
            appointments_created += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cleanup completed:\n'
                    f'- Deleted {appointments_deleted} test appointments\n'
                    f'- Deleted {payments_deleted} test payments\n'
                    f'- Created {appointments_created} realistic appointments\n'
                    f'- Created {payments_created} associated payments'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cleanup completed:\n'
                    f'- Deleted {appointments_deleted} test appointments\n'
                    f'- Deleted {payments_deleted} test payments\n'
                    f'- No new appointments created (no doctors/patients found)'
                )
            )
