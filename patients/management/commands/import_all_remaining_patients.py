from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import requests
import csv
from datetime import datetime, date
from patients.models import Patient

User = get_user_model()

class Command(BaseCommand):
    help = 'Import all remaining patients from Google Sheets into database'

    def handle(self, *args, **options):
        sheet_id = '1fYUdK_cprGPj8UEoZVI38DiqI7P4G_loOXf8Xg62TWc'
        sheet_name = 'Sheet1'
        
        self.stdout.write(self.style.SUCCESS(f'Importing all remaining patients from Google Sheet: {sheet_id}'))
        
        # Construct the CSV export URL
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
        
        try:
            # Fetch CSV data
            response = requests.get(csv_url)
            response.raise_for_status()
            
            csv_text = response.text
            patients = self.parse_patient_csv(csv_text)
            
            if not patients:
                self.stdout.write(self.style.WARNING('No valid patients found in the Google Sheet'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(patients)} patients to import'))
            
            # Import patients
            imported_count = self.import_patients_to_db(patients)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} patients into database!'))
            self.stdout.write(self.style.SUCCESS('You can now view them at: http://localhost:8000/patients/'))
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch Google Sheet: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing patients: {e}'))

    def parse_patient_csv(self, csv_text):
        """Parse CSV text and return list of patient dictionaries"""
        lines = csv_text.split('\n')
        if len(lines) < 2:
            return []
        
        # Parse data rows
        patients = []
        for i, line in enumerate(lines[1:], start=2):  # Start at 2 for line numbers
            if not line.strip():
                continue
                
            values = self.parse_csv_line(line)
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
                self.stdout.write(self.style.WARNING(f'Error parsing line {i}: {e}'))
                continue
        
        return patients

    def parse_csv_line(self, line):
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

    def import_patients_to_db(self, patients):
        """Import patients into database"""
        imported_count = 0
        
        for patient_data in patients:
            try:
                # Parse date of birth from age
                date_of_birth = self.parse_age_to_date(patient_data['age'])
                
                # Convert gender
                gender = self.normalize_gender(patient_data['gender'])
                
                # Normalize status
                status = 'active' if patient_data['status'].lower() == 'active' else 'inactive'
                
                # Create user account for the patient
                email = f"{patient_data['first_name'].lower().replace(' ', '')}.{patient_data['last_name'].lower().replace(' ', '')}@clinic.com"
                
                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    # Add number to make unique
                    counter = 1
                    base_email = email.split('@')[0]
                    while User.objects.filter(email=f"{base_email}{counter}@clinic.com").exists():
                        counter += 1
                    email = f"{base_email}{counter}@clinic.com"
                
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
                
                if imported_count % 500 == 0:
                    self.stdout.write(self.style.SUCCESS(f'Progress: {imported_count} patients imported...'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error importing patient at line {patient_data.get("line_number", "unknown")}: {e}'))
                continue
        
        return imported_count

    def parse_age_to_date(self, age_str):
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

    def normalize_gender(self, gender_str):
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
