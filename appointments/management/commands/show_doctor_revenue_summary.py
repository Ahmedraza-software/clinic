from django.core.management.base import BaseCommand
from patients.models import DoctorPayment
from datetime import date


class Command(BaseCommand):
    help = 'Show current doctor revenue summary'

    def handle(self, *args, **options):
        # Get current month
        today = date.today()
        current_month = today.replace(day=1)
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n📊 CURRENT DOCTOR REVENUE SUMMARY\n'
                '==================================\n'
            )
        )
        
        doctor_payments = DoctorPayment.objects.filter(payment_period=current_month)
        
        if not doctor_payments.exists():
            self.stdout.write(
                self.style.WARNING('No doctor revenue data found for this month.')
            )
            return
        
        total_revenue = sum(dp.revenue_generated for dp in doctor_payments)
        total_clinic_share = sum(dp.clinic_share for dp in doctor_payments)
        total_doctor_payouts = sum(dp.doctor_payout for dp in doctor_payments)
        
        self.stdout.write(f'📅 Period: {current_month.strftime("%B %Y")}\n')
        
        for i, doctor_payment in enumerate(doctor_payments.order_by('-revenue_generated'), 1):
            doctor_name = doctor_payment.doctor.user.get_full_name() if doctor_payment.doctor.user else 'Unknown'
            
            self.stdout.write(
                f'{i}. 👨‍⚕️ Dr. {doctor_name}\n'
                f'   💰 Revenue Generated: ${doctor_payment.revenue_generated:,.2f}\n'
                f'   🏥 Clinic Share (20%): ${doctor_payment.clinic_share:,.2f}\n'
                f'   💵 Doctor Payout (80%): ${doctor_payment.doctor_payout:,.2f}\n'
                f'   💳 Payment Status: {"✅ Paid" if doctor_payment.is_paid else "⏳ Pending"}\n'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📈 TOTALS:\n'
                f'=========\n'
                f'💰 Total Revenue Generated: ${total_revenue:,.2f}\n'
                f'🏥 Total Clinic Share (20%): ${total_clinic_share:,.2f}\n'
                f'💵 Total Doctor Payouts (80%): ${total_doctor_payouts:,.2f}\n'
                f'👨‍⚕️ Number of Doctors: {doctor_payments.count()}\n\n'
                f'🎯 This data now accurately reflects the payment history!\n'
            )
        )
