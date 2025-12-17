import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

from doctors.models import Specialization

# Common medical specializations
specializations = [
    'General Medicine',
    'Cardiology',
    'Dermatology',
    'Pediatrics',
    'Orthopedics',
    'Neurology',
    'Psychiatry',
    'Gynecology',
    'Oncology',
    'Radiology',
    'Surgery',
    'ENT (Ear, Nose, Throat)',
    'Ophthalmology',
    'Dentistry',
    'Emergency Medicine',
    'Internal Medicine',
    'Family Medicine',
    'Anesthesiology',
    'Pathology',
    'Urology',
]

print("Adding specializations...")
for spec_name in specializations:
    spec, created = Specialization.objects.get_or_create(name=spec_name)
    if created:
        print(f"✓ Added: {spec_name}")
    else:
        print(f"- Already exists: {spec_name}")

print(f"\nTotal specializations: {Specialization.objects.count()}")
print("Done!")
