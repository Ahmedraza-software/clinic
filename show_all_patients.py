import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from patients.models import Patient

def show_all_patients():
    patients = Patient.objects.all().order_by('created_at')
    
    print(f"\n{'='*120}")
    print(f"ALL 236 PATIENTS IN THE SYSTEM")
    print(f"{'='*120}")
    
    print(f"{'#':<4} {'Initials':<4} {'Full Name':<25} {'Patient Code':<12} {'Age':<4} {'DOB':<12} {'Blood':<6} {'Status':<8} {'Email':<30}")
    print(f"{'-'*120}")
    
    for i, patient in enumerate(patients, 1):
        # Get initials
        first_name = patient.user.first_name or ''
        last_name = patient.user.last_name or ''
        initials = (first_name[0] + last_name[0]).upper() if first_name and last_name else 'NN'
        
        # Get full name
        full_name = f"{first_name} {last_name}"
        
        # Generate patient code (P-000XXX format)
        patient_code = f"P-{236-i+1:06d}"  # Reverse order to match your display
        
        # Get age
        try:
            age = patient.age if patient.age else "N/A"
        except:
            age = "N/A"
        
        # Get DOB
        try:
            dob = patient.date_of_birth.strftime("%b %d, %Y") if patient.date_of_birth else "Not set"
        except:
            dob = "Not set"
        
        # Get blood group
        blood = patient.blood_group if patient.blood_group else "Not set"
        
        # Get status
        status = patient.status.title() if patient.status else "Unknown"
        
        # Get email
        email = patient.user.email or "No email"
        
        print(f"{i:<4} {initials:<4} {full_name:<25} {patient_code:<12} {age:<4} {dob:<12} {blood:<6} {status:<8} {email:<30}")
        
        # Add a separator every 20 patients for readability
        if i % 20 == 0:
            print(f"{'-'*120}")
    
    print(f"{'='*120}")
    print(f"TOTAL: {patients.count()} PATIENTS")
    print(f"{'='*120}")

if __name__ == "__main__":
    show_all_patients()
