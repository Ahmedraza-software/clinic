import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from patients.models import Patient

def check_patients():
    patients = Patient.objects.all().order_by('-created_at')
    
    print(f"\n{'='*80}")
    print(f"TOTAL PATIENTS IN SYSTEM: {patients.count()}")
    print(f"{'='*80}")
    
    if patients.count() == 0:
        print("No patients found in the system.")
        return
    
    print(f"\nLast 10 patients added:")
    print(f"{'Name':<25} {'Email':<30} {'Patient Code':<15} {'Created'}")
    print(f"{'-'*80}")
    
    for patient in patients[:10]:
        name = f"{patient.user.first_name} {patient.user.last_name}"
        email = patient.user.email
        created = patient.created_at.strftime("%Y-%m-%d %H:%M")
        
        # Try to get patient code from any field that might contain it
        patient_code = "N/A"
        if hasattr(patient, 'patient_code'):
            patient_code = patient.patient_code
        elif hasattr(patient.user, 'username') and patient.user.username:
            patient_code = patient.user.username
        
        print(f"{name:<25} {email:<30} {patient_code:<15} {created}")

if __name__ == "__main__":
    check_patients()
