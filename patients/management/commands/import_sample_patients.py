from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import requests
import csv
import io
from datetime import datetime, date
from patients.models import Patient

User = get_user_model()

class Command(BaseCommand):
    help = 'Import sample patients from Google Sheets CSV (first 10 records for testing)'

    def handle(self, *args, **options):
        sheet_id = '1fYUdK_cprGPj8UEoZVI38DiqI7P4G_loOXf8Xg62TWc'
        sheet_name = 'Sheet1'
        
        self.stdout.write(self.style.SUCCESS(f'Importing sample patients from Google Sheet: {sheet_id}'))
        
        # Construct the CSV export URL
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
        
        try:
            # Fetch CSV data
            response = requests.get(csv_url)
            response.raise_for_status()
            
            csv_text = response.text
            lines = csv_text.split('\n')
            
            # Only process first 11 lines (header + 10 patients)
            sample_lines = lines[:11]
            sample_text = '\n'.join(sample_lines)
            
            patients = self.parse_patient_csv(sample_text)
            
            if not patients:
                self.stdout.write(self.style.WARNING('No valid patients found in the sample'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(patients)} patients in sample to import'))
            
            # Import patients
            imported_count = self.import_patients(patients)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} sample patients!'))
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch Google Sheet: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing patients: {e}'))

    def parse_patient_csv(self, csv_text):
        """Parse CSV text and return list of patient dictionaries"""
        lines = csv_text.split('\n')
        if len(lines) < 2:
            return []
        
        # Parse headers (first row)
        headers = self.parse_csv_line(lines[0])
        
        # Parse data rows
        patients = []
        for i, line in enumerate(lines[1:], start=2):  # Start at 2 for line numbers
            if not line.strip():
                continue
                
            values = self.parse_csv_line(line)
            if len(values) < 6:  # Minimum required columns
                continue
            
            try:
                # Map the actual CSV columns to patient fields
                patient = {
                    'patient_code': values[0].strip() if len(values) > 0 else '',  # HMS code
                    'first_name': values[1].strip() if len(values) > 1 else '',
                    'last_name': values[2].strip() if len(values) > 2 else '',
                    'address': values[3].strip() if len(values) > 3 else '',
                    'gender': values[4].strip() if len(values) > 4 else '',
                    'date_of_birth': values[5].strip() if len(values) > 5 else '',
                    'phone': values[6].strip() if len(values) > 6 else '',
                    'emergency_contact': values[7].strip() if len(values) > 7 else '',
                    'cnic': values[8].strip() if len(values) > 8 else '',
                    'status': values[9].strip() if len(values) > 9 else 'active',
                    'line_number': i
                }
                
                # Generate email from name if not provided
                if patient['first_name'] and patient['last_name']:
                    # Clean the names for email
                    clean_first = patient['first_name'].lower().replace(' ', '').replace('.', '')
                    clean_last = patient['last_name'].lower().replace(' ', '').replace('.', '')
                    base_email = f"{clean_first}.{clean_last}@clinic.com"
                    patient['email'] = base_email
                else:
                    patient['email'] = f"patient.{patient['patient_code'].replace('-', '')}@clinic.com"
                
                # Validate required fields
                if patient['first_name'] and patient['last_name']:
                    patients.append(patient)
                    self.stdout.write(self.style.SUCCESS(f'Parsed: {patient["first_name"]} {patient["last_name"]} - {patient["patient_code"]}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Skipping line {i}: Missing required name fields'))
                    
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

    def import_patients(self, patients):
        """Import patients into the database"""
        imported_count = 0
        existing_emails = set(User.objects.values_list('email', flat=True))
        
        for patient_data in patients:
            try:
                # Check if email already exists
                if patient_data['email'] in existing_emails:
                    self.stdout.write(self.style.WARNING(f'Skipping {patient_data["email"]}: User already exists'))
                    continue
                
                # Parse date of birth
                date_of_birth = self.parse_date(patient_data['date_of_birth'])
                
                # Convert gender
                gender = self.normalize_gender(patient_data['gender'])
                
                # Normalize status
                status = 'active' if patient_data['status'].lower() == 'active' else 'inactive'
                
                # Create user
                user = User.objects.create_user(
                    email=patient_data['email'],
                    first_name=patient_data['first_name'],
                    last_name=patient_data['last_name'],
                    password='default123',  # Default password
                    is_active=True
                )
                
                # Create patient
                patient = Patient.objects.create(
                    user=user,
                    date_of_birth=date_of_birth,
                    gender=gender,
                    phone=patient_data['phone'],
                    address=patient_data['address'],
                    blood_group='O+',  # Default blood group since not in CSV
                    emergency_contact_name=patient_data['emergency_contact'],
                    emergency_contact_phone=patient_data['phone'],
                    status=status,
                    is_active=True
                )
                
                imported_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Imported: {patient_data["first_name"]} {patient_data["last_name"]} ({patient_data["email"]}) - Code: {patient_data["patient_code"]}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error importing {patient_data.get("email", "unknown")}: {e}'))
                continue
        
        return imported_count

    def parse_date(self, date_str):
        """Parse date string in various formats"""
        if not date_str:
            return None
        
        try:
            # If it's just a number (age), convert to approximate birth year
            if date_str.isdigit():
                age = int(date_str)
                birth_year = datetime.now().year - age
                return date(birth_year, 1, 1)  # Default to Jan 1st
            
            # Try different date formats
            formats = [
                '%Y-%m-%d',    # YYYY-MM-DD
                '%m/%d/%Y',    # MM/DD/YYYY
                '%d/%m/%Y',    # DD/MM/YYYY
                '%m-%d-%Y',    # MM-DD-YYYY
                '%d-%m-%Y',    # DD-MM-YYYY
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            self.stdout.write(self.style.WARNING(f'Could not parse date: {date_str}'))
            return None
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error parsing date {date_str}: {e}'))
            return None

    def normalize_gender(self, gender_str):
        """Normalize gender string to standard format"""
        if not gender_str:
            return 'O'
        
        gender_lower = gender_str.lower().strip()
        
        gender_map = {
            'male': 'M',
            'female': 'F',
            'm': 'M',
            'f': 'F',
            'man': 'M',
            'woman': 'F',
            'other': 'O',
            'o': 'O'
        }
        
        return gender_map.get(gender_lower, 'O')
