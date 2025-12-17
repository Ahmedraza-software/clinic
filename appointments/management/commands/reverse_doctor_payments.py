from django.core.management.base import BaseCommand
from patients.models import DoctorPayment, Expense
from datetime import date


class Command(BaseCommand):
    help = 'Reverse the last doctor payments and mark them as unpaid'

    def handle(self, *args, **options):
        # Get current month
        today = date.today()
        current_month = today.replace(day=1)
        
        # Find all paid doctor payments for this month
        paid_doctor_payments = DoctorPayment.objects.filter(
            payment_period=current_month,
            is_paid=True
        )
        
        if not paid_doctor_payments.exists():
            self.stdout.write(
                self.style.WARNING('No paid doctor payments found for this month.')
            )
            return
        
        reversed_count = 0
        total_reversed_amount = 0
        
        for doctor_payment in paid_doctor_payments:
            # Find and delete the corresponding expense record
            doctor_payout_expenses = Expense.objects.filter(
                category__name='Doctor Payouts',
                amount=doctor_payment.doctor_payout,
                expense_date__gte=current_month,
                description__icontains=doctor_payment.doctor.user.get_full_name() if doctor_payment.doctor.user else 'Unknown'
            )
            
            expenses_deleted = 0
            for expense in doctor_payout_expenses:
                self.stdout.write(
                    f'Deleting expense: {expense.description} - ${expense.amount}'
                )
                expense.delete()
                expenses_deleted += 1
            
            # Mark doctor payment as unpaid
            doctor_payment.is_paid = False
            doctor_payment.payment_date = None
            doctor_payment.notes = 'Payment reversed - marked as unpaid'
            doctor_payment.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Reversed payment for Dr. {doctor_payment.doctor}: ${doctor_payment.doctor_payout} '
                    f'(deleted {expenses_deleted} expense records)'
                )
            )
            
            reversed_count += 1
            total_reversed_amount += float(doctor_payment.doctor_payout)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully reversed {reversed_count} doctor payments\n'
                f'💰 Total amount reversed: ${total_reversed_amount:,.2f}\n'
                f'📊 All payments marked as unpaid and expense records removed'
            )
        )
