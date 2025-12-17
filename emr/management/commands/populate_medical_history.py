from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from patients.models import Patient
from emr.models import MedicalHistoryRecord, PatientAllergy, PatientMedication
import random

class Command(BaseCommand):
    help = 'Populate database with sample medical history data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample medical history data...')
        
        # Get or create a sample patient
        patients = Patient.objects.all()
        if not patients.exists():
            self.stdout.write(self.style.ERROR('No patients found. Please create patients first.'))
            return
        
        # Use the first patient for demo
        patient = patients.first()
        
        # Create sample medical history records
        self.create_medical_records(patient)
        
        # Create sample allergies
        self.create_allergies(patient)
        
        # Create sample medications
        self.create_medications(patient)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created sample medical history for {patient.full_name}')
        )

    def create_medical_records(self, patient):
        """Create sample medical history records"""
        records_data = [
            {
                'record_type': 'consultation',
                'date': timezone.now().date() - timedelta(days=3),
                'doctor_name': 'Dr. Smith',
                'diagnosis': 'Annual Checkup - Patient in good health',
                'treatment': 'Continue current medications, follow up in 6 months',
                'status': 'completed'
            },
            {
                'record_type': 'lab_test',
                'date': timezone.now().date() - timedelta(days=24),
                'doctor_name': 'Dr. Johnson',
                'diagnosis': 'Blood Work - Complete Blood Count and Lipid Panel',
                'treatment': 'Results within normal limits',
                'status': 'completed'
            },
            {
                'record_type': 'procedure',
                'date': timezone.now().date() - timedelta(days=48),
                'doctor_name': 'Dr. Williams',
                'diagnosis': 'Minor Surgery - Skin lesion removal',
                'treatment': 'Successful removal, wound healing well',
                'status': 'completed'
            },
            {
                'record_type': 'consultation',
                'date': timezone.now().date() - timedelta(days=90),
                'doctor_name': 'Dr. Brown',
                'diagnosis': 'Hypertension follow-up',
                'treatment': 'Blood pressure well controlled, continue current regimen',
                'status': 'completed'
            },
            {
                'record_type': 'lab_test',
                'date': timezone.now().date() - timedelta(days=120),
                'doctor_name': 'Dr. Davis',
                'diagnosis': 'Diabetes screening - HbA1c test',
                'treatment': 'Normal results, no diabetes detected',
                'status': 'completed'
            }
        ]
        
        for record_data in records_data:
            MedicalHistoryRecord.objects.get_or_create(
                patient=patient,
                record_type=record_data['record_type'],
                date=record_data['date'],
                defaults={
                    'doctor_name': record_data['doctor_name'],
                    'diagnosis': record_data['diagnosis'],
                    'treatment': record_data['treatment'],
                    'status': record_data['status'],
                    'time': timezone.now().time()
                }
            )

    def create_allergies(self, patient):
        """Create sample allergies"""
        allergies_data = [
            {
                'allergen': 'Penicillin',
                'allergy_type': 'drug',
                'severity': 'severe',
                'reaction': 'Severe skin rash, difficulty breathing, swelling'
            },
            {
                'allergen': 'Peanuts',
                'allergy_type': 'food',
                'severity': 'moderate',
                'reaction': 'Swelling, hives, stomach upset'
            },
            {
                'allergen': 'Dust Mites',
                'allergy_type': 'environmental',
                'severity': 'mild',
                'reaction': 'Sneezing, runny nose, watery eyes'
            }
        ]
        
        for allergy_data in allergies_data:
            PatientAllergy.objects.get_or_create(
                patient=patient,
                allergen=allergy_data['allergen'],
                defaults={
                    'allergy_type': allergy_data['allergy_type'],
                    'severity': allergy_data['severity'],
                    'reaction': allergy_data['reaction'],
                    'date_identified': timezone.now().date() - timedelta(days=random.randint(30, 365)),
                    'is_active': True
                }
            )

    def create_medications(self, patient):
        """Create sample current medications"""
        medications_data = [
            {
                'medication_name': 'Lisinopril',
                'dosage': '10mg',
                'frequency': 'once_daily',
                'indication': 'For high blood pressure',
                'prescribed_by_name': 'Dr. Smith',
                'start_date': timezone.now().date() - timedelta(days=60)
            },
            {
                'medication_name': 'Atorvastatin',
                'dosage': '20mg',
                'frequency': 'once_daily',
                'indication': 'For high cholesterol',
                'prescribed_by_name': 'Dr. Johnson',
                'start_date': timezone.now().date() - timedelta(days=90)
            },
            {
                'medication_name': 'Metformin',
                'dosage': '500mg',
                'frequency': 'twice_daily',
                'indication': 'For diabetes management',
                'prescribed_by_name': 'Dr. Brown',
                'start_date': timezone.now().date() - timedelta(days=120)
            }
        ]
        
        for med_data in medications_data:
            PatientMedication.objects.get_or_create(
                patient=patient,
                medication_name=med_data['medication_name'],
                defaults={
                    'dosage': med_data['dosage'],
                    'frequency': med_data['frequency'],
                    'indication': med_data['indication'],
                    'prescribed_by_name': med_data['prescribed_by_name'],
                    'start_date': med_data['start_date'],
                    'status': 'active',
                    'route': 'Oral'
                }
            )
