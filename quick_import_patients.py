#!/usr/bin/env python
import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from django.contrib.auth.models import User
from patients.models import Patient
from accounts.models import CustomUser

# Sample data for quick generation
FIRST_NAMES = ['Muhammad', 'Ahmed', 'Fatima', 'Ayesha', 'Ali', 'Zainab', 'Hassan', 'Zara', 'Omar', 'Khadija',
               'Bilal', 'Maryam', 'Usman', 'Aisha', 'Abdullah', 'Sana', 'Zaid', 'Hira', 'Yusuf', 'Sofia',
               'Hamza', 'Ibrahim', 'Sara', 'David', 'Yusuf', 'Layla', 'Adam', 'Noah', 'Musa', 'Hana']

LAST_NAMES = ['Khan', 'Ali', 'Ahmed', 'Hassan', 'Patel', 'Muhammad', 'Singh', 'Shah', 'Ansari', 'Qureshi',
              'Malik', 'Butt', 'Gill', 'Rehman', 'Iqbal', 'Younis', 'Farooq', 'Aziz', 'Baig', 'Chaudhary']

DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'clinic.com']

BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
GENDERS = ['Male', 'Female']

def generate_random_date():
    """Generate random date of birth between 18-80 years old"""
    today = datetime.now()
    days_18_years = 18 * 365
    days_80_years = 80 * 365
    random_days = random.randint(days_18_years, days_80_years)
    birth_date = today - timedelta(days=random_days)
    return birth_date

def generate_phone_number():
    """Generate random phone number"""
    return f"+92-3{random.randint(1,9)}{random.randint(100000000, 999999999)}"

def quick_import_patients(count=1000):
    """Quickly import specified number of patients"""
    print(f"Starting quick import of {count} patients...")
    
    imported = 0
    skipped = 0
    start_count = CustomUser.objects.count() + 1
    
    for i in range(count):
        # Generate random patient data
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        # Use incremental number for unique emails
        email = f"patient{start_count + i}@clinic.com"
        
        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            skipped += 1
            continue
        
        # Create user
        try:
            user = CustomUser.objects.create_user(
                email=email,
                password='default123',
                first_name=first_name,
                last_name=last_name
            )
            
            # Create patient
            birth_date = generate_random_date()
            patient = Patient.objects.create(
                user=user,
                phone=generate_phone_number(),
                address=f"Street {random.randint(1,100)}, Block {random.choice(['A', 'B', 'C', 'D'])}, {random.choice(['Karachi', 'Lahore', 'Islamabad', 'Rawalpindi'])}",
                date_of_birth=birth_date,
                gender=random.choice(['M', 'F', 'O']),
                blood_group=random.choice(BLOOD_GROUPS),
                emergency_contact_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                emergency_contact_phone=generate_phone_number(),
                status='active',
                is_active=True
            )
            
            imported += 1
            
            # Progress indicator
            if imported % 100 == 0:
                print(f"Imported {imported} patients...")
                
        except Exception as e:
            skipped += 1
            continue
    
    print(f"\n✅ Import Complete!")
    print(f"📊 Successfully imported: {imported} patients")
    print(f"⚠️  Skipped: {skipped} patients")
    print(f"🏥 Total patients in database: {Patient.objects.filter(is_active=True).count()}")

if __name__ == '__main__':
    # Import 1000 patients quickly
    quick_import_patients(1000)
