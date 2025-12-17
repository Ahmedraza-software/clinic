#!/usr/bin/env python
"""
Import patients from Google Sheets with comprehensive duplicate prevention
"""
import os
import sys
import django
import requests
import csv
from datetime import datetime, date

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from patients.models import Patient

User = get_user_model()

def parse_csv_line(line):
    """Parse a CSV line handling quotes and commas"""
    result = []
    current = ''
    in_quotes = False
    
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            result.append(current.strip())
            current = ''
        else:
            current += char
    
    result.append(current.strip())
    return result

def normalize_gender(gender_str):
    """Normalize gender string"""
    if not gender_str:
        return 'O'
    
    gender_lower = gender_str.lower().strip()
    
    if gender_lower in ['male', 'm']:
        return 'M'
    elif gender_lower in ['female', 'f']:
        return 'F'
    else:
        return 'O'

def parse_age_to_date(age_str):
    """Convert age to approximate birth date"""
    if not age_str or not age_str.isdigit():
        return None
    
    try:
        age = int(age_str)
        current_year = datetime.now().year
        birth_year = current_year - age
        return date(birth_year, 1, 1)  # Default to January 1st
    except:
        return None

def is_duplicate_patient(patient_data):
    """Check if patient already exists based on multiple criteria"""
    first_name = patient_data['first_name'].strip().lower()
    last_name = patient_data['last_name'].strip().lower()
    phone = patient_data['phone'].strip()
    cnic = patient_data['cnic'].strip()
    
    # Check by exact name match
    if Patient.objects.filter(
        user__first_name__iexact=first_name,
        user__last_name__iexact=last_name
    ).exists():
        return True, "Name already exists"
    
    # Check by phone number
    if phone and Patient.objects.filter(phone__iexact=phone).exists():
        return True, "Phone number already exists"
    
    # Check by email (generated from name)
    email = f"{first_name.replace(' ', '')}.{last_name.replace(' ', '')}@clinic.com"
    if User.objects.filter(email__iexact=email).exists():
        return True, "Email already exists"
    
    # Check by CNIC if available
    if cnic and hasattr(Patient, 'cnic'):
        if Patient.objects.filter(cnic__iexact=cnic).exists():
            return True, "CNIC already exists"
    
    return False, ""

def import_patients_no_duplicates():
    """Import patients with comprehensive duplicate checking"""
    sheet_id = '1fYUdK_cprGPj8UEoZVI38DiqI7P4G_loOXf8Xg62TWc'
    sheet_name = 'Sheet1'
    
    print("🏥 Importing patients from Google Sheets with duplicate prevention...")
    print("=" * 60)
    
    # Construct the CSV export URL
    csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    
    try:
        # Fetch CSV data
        print("📥 Fetching data from Google Sheets...")
        response = requests.get(csv_url)
        response.raise_for_status()
        
        csv_text = response.text
        lines = csv_text.split('\n')
        
        if len(lines) < 2:
            print("⚠️  No valid patients found in the Google Sheet")
            return
        
        # Parse data rows
        patients = []
        for i, line in enumerate(lines[1:], start=2):  # Start at 2 for line numbers
            if not line.strip():
                continue
                
            values = parse_csv_line(line)
            if len(values) < 10:  # Minimum required columns
                continue
            
            try:
                patient = {
                    'patient_code': values[0].strip() if len(values) > 0 else '',
                    'first_name': values[1].strip() if len(values) > 1 else '',
                    'last_name': values[2].strip() if len(values) > 2 else '',
                    'address': values[3].strip() if len(values) > 3 else '',
                    'gender': values[4].strip() if len(values) > 4 else '',
                    'age': values[5].strip() if len(values) > 5 else '',
                    'phone': values[6].strip() if len(values) > 6 else '',
                    'emergency_contact': values[7].strip() if len(values) > 7 else '',
                    'cnic': values[8].strip() if len(values) > 8 else '',
                    'status': values[9].strip() if len(values) > 9 else 'Active',
                    'line_number': i
                }
                
                # Validate required fields
                if patient['first_name'] and patient['last_name']:
                    patients.append(patient)
                    
            except Exception as e:
                print(f"⚠️  Error parsing line {i}: {e}")
                continue
        
        print(f"📊 Found {len(patients)} patients in Google Sheet")
        
        # Get current patient count
        initial_count = Patient.objects.filter(is_active=True).count()
        print(f"📈 Current patients in database: {initial_count}")
        
        # Import patients with duplicate checking
        imported_count = 0
        duplicate_count = 0
        error_count = 0
        
        print("\n🔄 Processing patients...")
        
        for patient_data in patients:
            try:
                # Check for duplicates
                is_duplicate, reason = is_duplicate_patient(patient_data)
                if is_duplicate:
                    duplicate_count += 1
                    if duplicate_count <= 10:  # Show first 10 duplicates
                        print(f"⚠️  Skipping duplicate: {patient_data['first_name']} {patient_data['last_name']} ({reason})")
                    continue
                
                # Parse date of birth from age
                date_of_birth = parse_age_to_date(patient_data['age'])
                
                # Convert gender
                gender = normalize_gender(patient_data['gender'])
                
                # Normalize status
                status = 'active' if patient_data['status'].lower() == 'active' else 'inactive'
                
                # Create unique email
                first_name_clean = patient_data['first_name'].lower().replace(' ', '')
                last_name_clean = patient_data['last_name'].lower().replace(' ', '')
                base_email = f"{first_name_clean}.{last_name_clean}@clinic.com"
                
                # Ensure email is unique
                email = base_email
                counter = 1
                while User.objects.filter(email=email).exists():
                    email = f"{first_name_clean}.{last_name_clean}{counter}@clinic.com"
                    counter += 1
                
                # Create user account
                user = User.objects.create_user(
                    email=email,
                    first_name=patient_data['first_name'],
                    last_name=patient_data['last_name'],
                    password='default123',
                    is_active=True
                )
                
                # Create patient record
                patient = Patient.objects.create(
                    user=user,
                    date_of_birth=date_of_birth,
                    gender=gender,
                    phone=patient_data['phone'],
                    address=patient_data['address'],
                    blood_group='O+',  # Default blood group
                    emergency_contact_name=patient_data['emergency_contact'],
                    emergency_contact_phone=patient_data['emergency_contact'] or patient_data['phone'],
                    status=status,
                    is_active=True
                )
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    print(f"✅ Imported {imported_count} new patients...")
                
            except Exception as e:
                error_count += 1
                print(f"❌ Error importing patient at line {patient_data.get('line_number', 'unknown')}: {e}")
                continue
        
        # Final statistics
        final_count = Patient.objects.filter(is_active=True).count()
        
        print("\n" + "=" * 60)
        print("📈 Import Summary:")
        print(f"   Initial patients: {initial_count}")
        print(f"   Successfully imported: {imported_count}")
        print(f"   Duplicates skipped: {duplicate_count}")
        print(f"   Errors: {error_count}")
        print(f"   Final patient count: {final_count}")
        print(f"   Net increase: {final_count - initial_count}")
        
        if imported_count > 0:
            print(f"\n🎉 Successfully imported {imported_count} new patients!")
        else:
            print(f"\n⚠️  No new patients were imported (all were duplicates or had errors)")
        
        print(f"📊 Total patients in system: {final_count}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch Google Sheet: {e}")
    except Exception as e:
        print(f"❌ Error importing patients: {e}")

if __name__ == "__main__":
    import_patients_no_duplicates()
