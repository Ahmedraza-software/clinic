#!/usr/bin/env python
"""
Quick script to add sample patients to the clinic system
"""
import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from patients.models import Patient

User = get_user_model()

def add_sample_patients(count=5000):
    """Add sample patients to the system"""
    print(f"🏥 Adding {count} sample patients to the clinic system...")
    
    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'James', 'Mary', 
                   'William', 'Jennifer', 'Richard', 'Linda', 'Joseph', 'Patricia', 'Thomas', 'Barbara', 'Charles', 'Susan',
                   'Christopher', 'Jessica', 'Daniel', 'Ashley', 'Matthew', 'Kimberly', 'Anthony', 'Donna', 'Mark', 'Carol',
                   'Steven', 'Michelle', 'Paul', 'Emily', 'Andrew', 'Amanda', 'Joshua', 'Melissa', 'Kevin', 'Deborah']
    
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris',
                  'Clark', 'Lewis', 'Robinson', 'Walker', 'Hall', 'Allen', 'Young', 'King', 'Scott', 'Green']
    
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    genders = ['M', 'F']
    
    initial_count = Patient.objects.filter(is_active=True).count()
    print(f"📊 Current patient count: {initial_count}")
    
    imported_count = 0
    
    for i in range(count):
        try:
            # Generate random patient data
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Generate unique email
            base_email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1000, 9999)}@clinic.com"
            
            # Create user account
            user = User.objects.create_user(
                email=base_email,
                password='defaultpassword123',
                first_name=first_name,
                last_name=last_name
            )
            
            # Generate random date of birth (ages 18-80)
            days_old = random.randint(6570, 29200)  # 18-80 years in days
            date_of_birth = datetime.now().date() - timedelta(days=days_old)
            
            # Create patient profile
            patient = Patient.objects.create(
                user=user,
                date_of_birth=date_of_birth,
                gender=random.choice(genders),
                blood_group=random.choice(blood_groups),
                phone=f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                address=f"{random.randint(100, 9999)} Main St, City {random.randint(1, 100)}, State {random.randint(1, 50)}",
                emergency_contact_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                emergency_contact_phone=f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                is_active=True
            )
            
            imported_count += 1
            if imported_count % 500 == 0:
                print(f"✅ Added {imported_count}/{count} patients...")
                
        except Exception as e:
            print(f"❌ Error creating patient {i}: {e}")
    
    final_count = Patient.objects.filter(is_active=True).count()
    
    print("\n" + "=" * 50)
    print("📈 Import Summary:")
    print(f"   Initial patients: {initial_count}")
    print(f"   Successfully imported: {imported_count}")
    print(f"   Final patient count: {final_count}")
    print(f"   Net increase: {final_count - initial_count}")
    
    print(f"\n🎉 Successfully added {imported_count} sample patients to the system!")
    print(f"📊 Total patients in system: {final_count}")

if __name__ == "__main__":
    add_sample_patients(5000)
