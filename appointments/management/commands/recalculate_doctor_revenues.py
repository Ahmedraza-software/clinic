from django.core.management.base import BaseCommand
from appointments.models import Appointment
from patients.models import DoctorPayment, PatientPayment
from doctors.models import Doctor
from decimal import Decimal
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Recalculate doctor revenues based on existing payment data'

    def handle(self, *args, **options):
        # Get current month
        today = date.today()
        current_month = today.replace(day=1)
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🔄 RECALCULATING DOCTOR REVENUES\n'
                '================================\n'
            )
        )
        
        # Clear existing doctor payment records for this month
        existing_records = DoctorPayment.objects.filter(payment_period=current_month)
        deleted_count = existing_records.count()
        existing_records.delete()
        
        self.stdout.write(f'🗑️  Cleared {deleted_count} existing doctor payment records')
        
        # Get all doctors
        doctors = Doctor.objects.select_related('user').filter(user__is_active=True)
        
        total_revenue_calculated = Decimal('0')
        
        for doctor in doctors:
            doctor_name = doctor.user.get_full_name() if doctor.user else str(doctor)
            
            # Find all payments that mention this doctor
            doctor_payments = PatientPayment.objects.filter(
                payment_date__gte=current_month,
                notes__icontains=doctor_name
            )
            
            # Also find consultation fees from completed appointments with this doctor
            completed_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date__gte=current_month,
                status='completed'
            )
            
            appointment_payments = []
            for appointment in completed_appointments:
                # Look for payments around appointment date
                payments = PatientPayment.objects.filter(
                    patient=appointment.patient,
                    payment_date__gte=appointment.appointment_date - timedelta(days=7),
                    payment_date__lte=appointment.appointment_date + timedelta(days=7),
                    payment_type__in=['consultation_fee', 'appointment_fee']
                )
                appointment_payments.extend(payments)
            
            # Combine and deduplicate payments
            all_payments = list(doctor_payments) + appointment_payments
            unique_payments = list({payment.id: payment for payment in all_payments}.values())
            
            # Calculate total revenue for this doctor
            doctor_revenue = sum(payment.amount for payment in unique_payments)
            
            if doctor_revenue > 0:
                # Create DoctorPayment record
                doctor_payment = DoctorPayment.objects.create(
                    doctor=doctor,
                    payment_period=current_month,
                    revenue_generated=doctor_revenue,
                    clinic_share=doctor_revenue * Decimal('0.20'),
                    doctor_payout=doctor_revenue * Decimal('0.80'),
                    is_paid=False
                )
                
                total_revenue_calculated += doctor_revenue
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Dr. {doctor_name}: ${doctor_revenue:,.2f} '
                        f'({len(unique_payments)} payments)'
                    )
                )
                
                # Show payment details
                for payment in unique_payments:
                    self.stdout.write(
                        f'   💰 ${payment.amount} - {payment.notes[:50]}...'
                    )
            else:
                self.stdout.write(f'⚪ Dr. {doctor_name}: No revenue found')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 RECALCULATION COMPLETE!\n'
                f'==========================\n'
                f'💰 Total Revenue Calculated: ${total_revenue_calculated:,.2f}\n'
                f'👨‍⚕️ Doctors with Revenue: {DoctorPayment.objects.filter(payment_period=current_month).count()}\n'
                f'📊 The finance dashboard will now show accurate doctor revenues!\n'
            )
        )
