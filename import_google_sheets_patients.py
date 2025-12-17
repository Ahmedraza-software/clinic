#!/usr/bin/env python
"""
Import patients from Google Sheets to the clinic database
"""
import os
import sys
import django
import requests
import csv
import io
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from patients.models import Patient

User = get_user_model()

def fetch_google_sheets_data():
    """Fetch patient data from Google Sheets"""
    sheet_id = '1fYdK_cprGPj8UEoZVI38DiqI7P4G_loOXf8Xg62TWc'
    sheet_name = 'Sheet1'
    
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
    """Create a patient from Google Sheets data"""
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
            password='defaultpassword123',  # Default password, can be changed later
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

def import_patients():
    """Main import function"""
    print("🏥 Starting Google Sheets Patient Import")
    print("=" * 50)
    
    # Fetch data from Google Sheets
    patients_data = fetch_google_sheets_data()
    if not patients_data:
        print("❌ Import failed: Could not fetch data from Google Sheets")
        return
    
    # Get current patient count
    initial_count = Patient.objects.filter(is_active=True).count()
    print(f"📊 Current patient count: {initial_count}")
    
    # Import patients
    imported_count = 0
    skipped_count = 0
    
    print("\n🔄 Importing patients...")
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
            print(f"✅ Imported {i}/{len(patients_data)}: {patient.user.get_full_name()}")
        else:
            skipped_count += 1
            print(f"❌ Failed to import {i}/{len(patients_data)}: {patient_data.get('first_name', 'Unknown')} {patient_data.get('last_name', 'Unknown')}")
    
    # Final statistics
    final_count = Patient.objects.filter(is_active=True).count()
    print("\n" + "=" * 50)
    print("📈 Import Summary:")
    print(f"   Initial patients: {initial_count}")
    print(f"   Successfully imported: {imported_count}")
    print(f"   Skipped/Failed: {skipped_count}")
    print(f"   Final patient count: {final_count}")
    print(f"   Net increase: {final_count - initial_count}")
    
    if imported_count > 0:
        print(f"\n🎉 Successfully imported {imported_count} patients from Google Sheets!")
    else:
        print(f"\n⚠️  No new patients were imported.")

if __name__ == "__main__":
    import_patients()
