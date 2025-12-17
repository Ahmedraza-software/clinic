from django.core.management.base import BaseCommand
import requests
import csv
from patients.models import Patient

class Command(BaseCommand):
    help = 'Import raw patient data from Google Sheets CSV'

    def handle(self, *args, **options):
        sheet_id = '1fYUdK_cprGPj8UEoZVI38DiqI7P4G_loOXf8Xg62TWc'
        sheet_name = 'Sheet1'
        
        self.stdout.write(self.style.SUCCESS(f'Importing raw patients from Google Sheet: {sheet_id}'))
        
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
            imported_count = self.import_raw_patients(patients)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} raw patients from Google Sheet!'))
            
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
        self.stdout.write(self.style.SUCCESS(f'Headers: {headers}'))
        
        # Parse data rows
        patients = []
        for i, line in enumerate(lines[1:], start=2):  # Start at 2 for line numbers
            if not line.strip():
                continue
                
            values = self.parse_csv_line(line)
            if len(values) < 10:  # Minimum required columns
                continue
            
            try:
                # Import exactly as in CSV
                patient = {
                    'id': values[0].strip() if len(values) > 0 else '',
                    'fname': values[1].strip() if len(values) > 1 else '',
                    'lname': values[2].strip() if len(values) > 2 else '',
                    'address': values[3].strip() if len(values) > 3 else '',
                    'sex': values[4].strip() if len(values) > 4 else '',
                    'dob': values[5].strip() if len(values) > 5 else '',
                    'mobile': values[6].strip() if len(values) > 6 else '',
                    'emerg_contact': values[7].strip() if len(values) > 7 else '',
                    'cnic': values[8].strip() if len(values) > 8 else '',
                    'status': values[9].strip() if len(values) > 9 else '',
                    'remarks': values[10].strip() if len(values) > 10 else '',
                    'gurd': values[11].strip() if len(values) > 11 else '',
                    'father_name': values[12].strip() if len(values) > 12 else '',
                    'hsb_name': values[13].strip() if len(values) > 13 else '',
                    'marital_status': values[14].strip() if len(values) > 14 else '',
                    'created_date': values[15].strip() if len(values) > 15 else '',
                    'created_by': values[16].strip() if len(values) > 16 else '',
                    'acode': values[17].strip() if len(values) > 17 else '',
                    'line_number': i
                }
                
                # Validate required fields
                if patient['fname'] and patient['lname']:
                    patients.append(patient)
                    if len(patients) <= 5:  # Show first 5 for verification
                        self.stdout.write(self.style.SUCCESS(f'Parsed: {patient["fname"]} {patient["lname"]} - ID: {patient["id"]}'))
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

    def import_raw_patients(self, patients):
        """Import raw patients into a simple model or just display them"""
        imported_count = 0
        
        for patient_data in patients:
            try:
                # Just display the raw data for now
                if imported_count < 10:  # Show first 10
                    self.stdout.write(self.style.SUCCESS(f'''
Patient {imported_count + 1}:
  ID: {patient_data['id']}
  Name: {patient_data['fname']} {patient_data['lname']}
  Address: {patient_data['address']}
  Sex: {patient_data['sex']}
  DOB: {patient_data['dob']}
  Mobile: {patient_data['mobile']}
  Emergency Contact: {patient_data['emerg_contact']}
  CNIC: {patient_data['cnic']}
  Status: {patient_data['status']}
  Remarks: {patient_data['remarks']}
  Guardian: {patient_data['gurd']}
  Father Name: {patient_data['father_name']}
  Husband Name: {patient_data['hsb_name']}
  Marital Status: {patient_data['marital_status']}
  Created Date: {patient_data['created_date']}
  Created By: {patient_data['created_by']}
  Acode: {patient_data['acode']}
                    '''.strip()))
                
                imported_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing patient {patient_data.get("id", "unknown")}: {e}'))
                continue
        
        self.stdout.write(self.style.SUCCESS(f'Total patients available: {len(patients)}'))
        self.stdout.write(self.style.WARNING('To create database records, you need to map these fields to your Patient model'))
        
        return imported_count
