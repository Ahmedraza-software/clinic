import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from patients.models import Patient

def show_patients():
    patients = Patient.objects.all().order_by('-created_at')
    
    print(f"\n{'='*80}")
    print(f"TOTAL PATIENTS IN SYSTEM: {patients.count()}")
    print(f"{'='*80}")
    
    if patients.count() == 0:
        print("No patients found in the system.")
        return
    
    print(f"{'#':<3} {'Name':<25} {'Email':<30} {'Age':<5} {'Blood':<8} {'Status':<10} {'Created Date'}")
    print(f"{'-'*80}")
    
    for i, patient in enumerate(patients, 1):
        name = f"{patient.user.first_name} {patient.user.last_name}"
        email = patient.user.email
        age = patient.age if patient.age else "N/A"
        blood = patient.blood_group if patient.blood_group else "Not set"
        status = patient.status.title()
        created = patient.created_at.strftime("%Y-%m-%d %H:%M")
        
        print(f"{i:<3} {name:<25} {email:<30} {age:<5} {blood:<8} {status:<10} {created}")
    
    print(f"{'-'*80}")
    print(f"\nLast 5 patients added:")
    for patient in patients[:5]:
        print(f"- {patient.user.first_name} {patient.user.last_name} ({patient.user.email}) - Added {patient.created_at.strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    show_patients()
