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
    help = 'Import only 100 patients from Google Sheets CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sheet-id',
            type=str,
            default='1fYUdK_cprGPj8UEoZVI38DiqI7P4G_loOXf8Xg62TWc',
            help='Google Sheet ID (default: your sheet ID)'
        )
        parser.add_argument(
            '--sheet-name',
            type=str,
            default='Sheet1',
            help='Sheet name (default: Sheet1)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of patients to import (default: 100)'
        )

    def handle(self, *args, **options):
        sheet_id = options['sheet_id']
        sheet_name = options['sheet_name']
        limit = options['limit']
        
        self.stdout.write(self.style.SUCCESS(f'Importing max {limit} patients from Google Sheet: {sheet_id}'))
        
        # Construct the CSV export URL
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
        
        try:
            # Fetch CSV data
            response = requests.get(csv_url)
            response.raise_for_status()
            
            csv_text = response.text
            patients = self.parse_patient_csv(csv_text, limit)
            
            if not patients:
                self.stdout.write(self.style.WARNING('No valid patients found in the Google Sheet'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(patients)} patients to import (limited to {limit})'))
            
            # Import patients
            imported_count = self.import_patients(patients)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} patients from Google Sheet!'))
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch Google Sheet: {e}'))
            self.stdout.write(self.style.WARNING('\nTo fix this issue:'))
            self.stdout.write(self.style.WARNING('1. Open your Google Sheet'))
            self.stdout.write(self.style.WARNING('2. Go to File > Share > Publish to web'))
            self.stdout.write(self.style.WARNING('3. Under "Link" tab, select "Comma-separated values (.csv)"'))
            self.stdout.write(self.style.WARNING('4. Click "Publish"'))
            self.stdout.write(self.style.WARNING('5. Wait a few minutes and try again'))
            self.stdout.write(self.style.WARNING(f'\nSheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit'))
            self.stdout.write(self.style.WARNING(f'CSV URL: {csv_url}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing patients: {e}'))

    def parse_patient_csv(self, csv_text, limit):
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
            
            # Stop if we've reached the limit
            if len(patients) >= limit:
                break
            
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
                    'remarks': values[10].strip() if len(values) > 10 else '',
                    'guardian_relation': values[11].strip() if len(values) > 11 else '',
                    'father_name': values[12].strip() if len(values) > 12 else '',
                    'husband_name': values[13].strip() if len(values) > 13 else '',
                    'marital_status': values[14].strip() if len(values) > 14 else '',
                    'created_date': values[15].strip() if len(values) > 15 else '',
                    'created_by': values[16].strip() if len(values) > 16 else '',
                    'acode': values[17].strip() if len(values) > 17 else '',
                    'line_number': i
                }
                
                # Generate email from name if not provided
                if patient['first_name'] and patient['last_name']:
                    base_email = f"{patient['first_name'].lower()}.{patient['last_name'].lower()}@clinic.com"
                    # Remove special characters and spaces
                    base_email = ''.join(c for c in base_email if c.isalnum() or c in ['.', '@', '_'])
                    patient['email'] = base_email
                else:
                    patient['email'] = f"patient.{patient['patient_code']}@clinic.com"
                
                # Validate required fields
                if patient['first_name'] and patient['last_name']:
                    patients.append(patient)
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
        
        for patient_data in patients:
            try:
                # Check if email already exists
                if User.objects.filter(email=patient_data['email']).exists():
                    self.stdout.write(self.style.WARNING(f'Skipping {patient_data["email"]}: User already exists'))
                    continue
                
                # Parse date of birth
                date_of_birth = self.parse_date(patient_data['date_of_birth'])
                if not date_of_birth:
                    self.stdout.write(self.style.WARNING(f'Skipping {patient_data["email"]}: Invalid date of birth'))
                    continue
                
                # Convert gender
                gender = self.normalize_gender(patient_data['gender'])
                
                # Normalize status
                status = 'active' if patient_data['status'].lower() == 'active' else 'inactive'
                
                # Create user without password first
                user = User.objects.create_user(
                    email=patient_data['email'],
                    first_name=patient_data['first_name'],
                    last_name=patient_data['last_name'],
                    password='default123',  # Default password
                    is_active=True,
                    user_type='patient'
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
                    emergency_contact_phone=patient_data['phone'],  # Use phone as emergency contact if not specified
                    emergency_contact_relation=patient_data['guardian_relation'],
                    marital_status=patient_data['marital_status'],
                    status=status,
                    is_active=True
                )
                
                imported_count += 1
                self.stdout.write(self.style.SUCCESS(f'Imported: {patient_data["first_name"]} {patient_data["last_name"]} ({patient_data["email"]}) - Code: {patient_data["patient_code"]}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing {patient_data.get("email", "unknown")}: {e}'))
                continue
        
        return imported_count

    def parse_date(self, date_str):
        """Parse date string in various formats"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = [
                '%m/%d/%Y',    # MM/DD/YYYY
                '%d/%m/%Y',    # DD/MM/YYYY
                '%Y-%m-%d',    # YYYY-MM-DD
                '%m-%d-%Y',    # MM-DD-YYYY
                '%d-%m-%Y',    # DD-MM-YYYY
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # If all formats fail, try to parse as age
            if date_str.isdigit():
                age = int(date_str)
                birth_year = datetime.now().year - age
                return date(birth_year, 1, 1)  # Default to Jan 1st
            
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
