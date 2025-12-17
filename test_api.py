#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append('c:/Users/ahmed/Desktop/clinic')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')
django.setup()

# Test the refresh API
from clinic_project.views import refresh_financial_data
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from accounts.models import CustomUser

# Create a mock request
request = HttpRequest()
request.method = 'GET'

# Set a user (needed for login_required)
User = get_user_model()
request.user = User.objects.filter(is_staff=True).first()

if request.user:
    # Call the API
    response = refresh_financial_data(request)
    
    if hasattr(response, 'content'):
        import json
        data = json.loads(response.content.decode('utf-8'))
        
        if data.get('success'):
            print("✅ API Test Successful!")
            print(f"📊 Total Doctor Revenue: ${data['data']['total_doctor_revenue']:,.2f}")
            print(f"👨‍⚕️ Completed Appointments: {data['data']['total_completed_appointments']}")
            print(f"🏥 Clinic Share: ${data['data']['clinic_share']:,.2f}")
            print(f"💵 Doctor Payouts: ${data['data']['total_doctor_payouts']:,.2f}")
            
            if 'doctor_revenues' in data['data']:
                print(f"\n👨‍⚕️ Doctor Details:")
                for doctor in data['data']['doctor_revenues']:
                    print(f"  • {doctor['doctor_name']}: ${doctor['total_revenue']:,.2f}")
        else:
            print("❌ API Error:", data.get('error'))
    else:
        print("❌ Invalid response format")
else:
    print("❌ No admin user found for testing")
