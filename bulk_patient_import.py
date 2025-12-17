#!/usr/bin/env python
"""
Bulk Patient Import Script for Clinic Management System
Supports both Google Sheets import and local CSV file import
"""
import os
import sys
import django
import requests
import csv
import io
from datetime import datetime
import random

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from patients.models import Patient

User = get_user_model()

def generate_sample_patients(count=1000):
    """Generate sample patients for testing"""
    print(f"🔄 Generating {count} sample patients...")
    
    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'James', 'Mary', 
                   'William', 'Jennifer', 'Richard', 'Linda', 'Joseph', 'Patricia', 'Thomas', 'Barbara', 'Charles', 'Susan']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris']
    
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    genders = ['M', 'F', 'O']
    
    imported_count = 0
    
    for i in range(count):
        # Generate random patient data
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        # Generate unique email
        base_email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100, 999)}@clinic.com"
        
        # Create user account
        try:
            user = User.objects.create_user(
                email=base_email,
                password='defaultpassword123',
                first_name=first_name,
                last_name=last_name
            )
            
            # Generate random date of birth (ages 18-80)
            days_old = random.randint(6570, 29200)  # 18-80 years in days
            date_of_birth = datetime.now().date() - datetime.timedelta(days=days_old)
            
            # Create patient profile
            patient = Patient.objects.create(
                user=user,
                date_of_birth=date_of_birth,
                gender=random.choice(genders),
                blood_group=random.choice(blood_groups),
                phone=f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                address=f"{random.randint(100, 999)} Main St, City {random.randint(1, 100)}, State {random.randint(1, 50)}",
                emergency_contact_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                emergency_contact_phone=f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                is_active=True
            )
            
            imported_count += 1
            if imported_count % 100 == 0:
                print(f"✅ Generated {imported_count}/{count} patients...")
                
        except Exception as e:
            print(f"❌ Error creating patient {first_name} {last_name}: {e}")
    
    return imported_count

def fetch_google_sheets_data(sheet_id, sheet_name='Sheet1'):
    """Fetch patient data from Google Sheets"""
    # Construct the CSV export URL
    csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    
    try:
        print("📥 Fetching patient data from Google Sheets...")
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV data
        csv_data = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_data))
        
        patients = list(reader)
        print(f"✅ Successfully fetched {len(patients)} patient records from Google Sheets")
        return patients
        
    except requests.RequestException as e:
        print(f"❌ Error fetching data from Google Sheets: {e}")
        return None
    except Exception as e:
        print(f"❌ Error parsing CSV data: {e}")
        return None

def create_patient_from_data(patient_data):
    """Create a patient from CSV/Google Sheets data"""
    try:
        # Generate unique email
        base_email = patient_data.get('email', '').strip()
        if not base_email:
            # Generate email from name if not provided
            first_name = patient_data.get('first_name', '').strip()
            last_name = patient_data.get('last_name', '').strip()
            base_email = f"{first_name.lower()}.{last_name.lower()}@clinic.com"
        
        # Ensure email is unique
        email = base_email
        counter = 1
        while User.objects.filter(email=email).exists():
            email = f"{base_email.split('@')[0]}{counter}@{base_email.split('@')[1]}"
            counter += 1
        
        # Create user account
        user = User.objects.create_user(
            email=email,
            password='defaultpassword123',
            first_name=patient_data.get('first_name', '').strip(),
            last_name=patient_data.get('last_name', '').strip()
        )
        
        # Parse date of birth
        date_of_birth = None
        dob_str = patient_data.get('date_of_birth', '').strip()
        if dob_str:
            try:
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_of_birth = datetime.strptime(dob_str, fmt).date()
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Create patient profile
        patient = Patient.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            gender=patient_data.get('gender', 'O').strip().upper(),
            blood_group=patient_data.get('blood_group', 'O+').strip(),
            phone=patient_data.get('phone', '').strip(),
            address=patient_data.get('address', '').strip(),
            emergency_contact_name=patient_data.get('emergency_contact_name', '').strip(),
            emergency_contact_phone=patient_data.get('emergency_contact_phone', '').strip(),
            is_active=True
        )
        
        return patient
        
    except Exception as e:
        print(f"❌ Error creating patient {patient_data.get('first_name', 'Unknown')}: {e}")
        return None

def import_from_csv_file(csv_file_path):
    """Import patients from a local CSV file"""
    try:
        print(f"📥 Reading patient data from CSV file: {csv_file_path}")
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            patients = list(reader)
        
        print(f"✅ Successfully read {len(patients)} patient records from CSV file")
        return patients
        
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return None

def import_patients():
    """Main import function with multiple options"""
    print("🏥 Bulk Patient Import System")
    print("=" * 50)
    
    # Get current patient count
    initial_count = Patient.objects.filter(is_active=True).count()
    print(f"📊 Current patient count: {initial_count}")
    
    print("\n📋 Import Options:")
    print("1. Generate sample patients (for testing)")
    print("2. Import from Google Sheets")
    print("3. Import from local CSV file")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    patients_data = None
    import_source = ""
    
    if choice == '1':
        # Generate sample patients
        count = input("How many sample patients to generate? (default: 1000): ").strip()
        try:
            count = int(count) if count else 1000
        except ValueError:
            count = 1000
        
        print(f"\n🔄 Generating {count} sample patients...")
        imported_count = generate_sample_patients(count)
        
        # Final statistics
        final_count = Patient.objects.filter(is_active=True).count()
        print("\n" + "=" * 50)
        print("📈 Import Summary:")
        print(f"   Initial patients: {initial_count}")
        print(f"   Successfully generated: {imported_count}")
        print(f"   Final patient count: {final_count}")
        print(f"   Net increase: {final_count - initial_count}")
        return
        
    elif choice == '2':
        # Google Sheets import
        sheet_id = input("Enter Google Sheets ID (or press Enter for default): ").strip()
        if not sheet_id:
            sheet_id = '1fYdK_cprGPj8UEoZVI38DiqI7P4G_loOXf8Xg62TWc'
        
        sheet_name = input("Enter sheet name (default: Sheet1): ").strip()
        if not sheet_name:
            sheet_name = 'Sheet1'
        
        patients_data = fetch_google_sheets_data(sheet_id, sheet_name)
        import_source = "Google Sheets"
        
    elif choice == '3':
        # CSV file import
        csv_file = input("Enter CSV file path: ").strip()
        patients_data = import_from_csv_file(csv_file)
        import_source = "CSV file"
        
    else:
        print("❌ Invalid option selected")
        return
    
    if not patients_data:
        print(f"❌ Import failed: Could not fetch data from {import_source}")
        return
    
    # Import patients
    print(f"\n🔄 Importing patients from {import_source}...")
    imported_count = 0
    skipped_count = 0
    
    for i, patient_data in enumerate(patients_data, 1):
        # Skip if required fields are missing
        if not patient_data.get('first_name', '').strip() or not patient_data.get('last_name', '').strip():
            print(f"⚠️  Skipping row {i}: Missing required name fields")
            skipped_count += 1
            continue
        
        # Create patient
        patient = create_patient_from_data(patient_data)
        if patient:
            imported_count += 1
            if imported_count % 10 == 0:
                print(f"✅ Imported {imported_count}/{len(patients_data)} patients...")
        else:
            skipped_count += 1
    
    # Final statistics
    final_count = Patient.objects.filter(is_active=True).count()
    print("\n" + "=" * 50)
    print("📈 Import Summary:")
    print(f"   Import source: {import_source}")
    print(f"   Initial patients: {initial_count}")
    print(f"   Successfully imported: {imported_count}")
    print(f"   Skipped/Failed: {skipped_count}")
    print(f"   Final patient count: {final_count}")
    print(f"   Net increase: {final_count - initial_count}")
    
    if imported_count > 0:
        print(f"\n🎉 Successfully imported {imported_count} patients from {import_source}!")
    else:
        print(f"\n⚠️  No new patients were imported.")

if __name__ == "__main__":
    import_patients()
