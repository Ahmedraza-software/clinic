from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, date
from django.db.models import Count, Q
from django.core.paginator import Paginator
from .models import Donor, BloodTransfer

# Create your views here.

@login_required
def dashboard(request):
    """Blood Bank Dashboard - redirect to main blood transfer view"""
    return redirect('blood_transfer')

def get_donor_statistics():
    """Get donor statistics for dashboard"""
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    donors = Donor.objects.all()
    
    stats = {
        'total_donors': donors.count(),
        'donations_today': donors.filter(donation_date=today).count(),
        'donations_this_month': donors.filter(
            donation_date__month=current_month,
            donation_date__year=current_year
        ).count(),
        'total_donations': donors.aggregate(total=Count('id'))['total'] or 0,
    }
    return stats

def get_blood_inventory():
    """Get blood inventory counts - donated units minus transferred units"""
    from django.db.models import Sum
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    inventory = {}
    
    for blood_type in blood_types:
        # Sum the donation_count for all donors of this blood type
        total_donated = Donor.objects.filter(blood_group=blood_type).aggregate(Sum('donation_count'))['donation_count__sum']
        total_donated = total_donated if total_donated else 0
        
        # Sum the units transferred for this blood type
        total_transferred = BloodTransfer.objects.filter(blood_type=blood_type).aggregate(Sum('units'))['units__sum']
        total_transferred = total_transferred if total_transferred else 0
        
        # Available = Donated - Transferred (minimum 0, never negative)
        available = total_donated - total_transferred
        inventory[blood_type] = max(0, available)  # Never show negative inventory
    
    return inventory

def get_blood_flow_totals():
    """Get total units in (donated) and out (transferred)"""
    from django.db.models import Sum
    
    # Total units donated (sum of all donation_count)
    total_units_in = Donor.objects.aggregate(Sum('donation_count'))['donation_count__sum'] or 0
    
    # Total units transferred (sum of all transfer units)
    total_units_out = BloodTransfer.objects.aggregate(Sum('units'))['units__sum'] or 0
    
    return {
        'total_units_in': total_units_in,
        'total_units_out': total_units_out
    }

@require_http_methods(["GET"])
def donor_statistics_api(request):
    """API endpoint to get donor statistics"""
    stats = get_donor_statistics()
    return JsonResponse(stats)

@require_http_methods(["GET"])
def blood_inventory_api(request):
    """API endpoint to get blood inventory"""
    inventory = get_blood_inventory()
    return JsonResponse(inventory)

@require_http_methods(["GET"])
def blood_compatibility_api(request):
    """API endpoint to get blood compatibility and inventory for a specific blood type"""
    blood_type = request.GET.get('blood_type')
    
    if not blood_type:
        return JsonResponse({'error': 'Blood type parameter is required'}, status=400)
    
    # Blood compatibility rules
    compatibility_map = {
        'A+': ['A+', 'A-', 'O+', 'O-'],
        'A-': ['A-', 'O-'],
        'B+': ['B+', 'B-', 'O+', 'O-'],
        'B-': ['B-', 'O-'],
        'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],  # Universal recipient
        'AB-': ['A-', 'B-', 'AB-', 'O-'],
        'O+': ['O+', 'O-'],
        'O-': ['O-']  # Universal donor (can only receive O-)
    }
    
    # Get full inventory
    inventory = get_blood_inventory()
    
    # Get compatible blood types for the patient
    compatible_types = compatibility_map.get(blood_type, [blood_type])
    
    # Build response with compatibility info
    response_data = {
        'patient_blood_type': blood_type,
        'patient_inventory': inventory.get(blood_type, 0),
        'compatible_types': {},
        'total_compatible_units': 0,
        'emergency_compatible': []
    }
    
    total_units = 0
    for compatible_type in compatible_types:
        units = inventory.get(compatible_type, 0)
        response_data['compatible_types'][compatible_type] = units
        total_units += units
        
        # Mark emergency compatible types (O- for everyone, patient's type priority)
        if compatible_type == 'O-' or compatible_type == blood_type:
            if units > 0:
                response_data['emergency_compatible'].append({
                    'type': compatible_type,
                    'units': units,
                    'priority': 'high' if compatible_type == blood_type else 'universal'
                })
    
    response_data['total_compatible_units'] = total_units
    
    # Add status information
    if response_data['patient_inventory'] == 0:
        response_data['status'] = 'out_of_stock'
        response_data['message'] = f"No {blood_type} blood available"
    elif response_data['patient_inventory'] < 3:
        response_data['status'] = 'low_stock'
        response_data['message'] = f"Low stock: Only {response_data['patient_inventory']} units of {blood_type} available"
    else:
        response_data['status'] = 'available'
        response_data['message'] = f"{response_data['patient_inventory']} units of {blood_type} available"
    
    return JsonResponse(response_data)

@csrf_exempt
@require_http_methods(["POST"])
def add_donor_api(request):
    """API endpoint to add a new donor"""
    try:
        # Extract form data
        data = request.POST
        
        # Debug: Print received donation_count
        donation_count = int(data.get('donation_count', 0))
        blood_group = data.get('blood_group')
        print(f"Adding donor: {data.get('full_name')}, blood_group: {blood_group}, donation_count: {donation_count}")
        
        # Create new donor
        donor = Donor.objects.create(
            full_name=data.get('full_name'),
            age=int(data.get('age')),
            gender=data.get('gender'),
            phone=data.get('phone'),
            blood_group=blood_group,
            weight=float(data.get('weight')),
            donation_count=donation_count,
            donation_type=data.get('donation_type', 'whole'),
            donation_date=data.get('donation_date') or timezone.now().date(),
            donation_time=data.get('donation_time') or timezone.now().time(),
            email=data.get('email', ''),
            address=data.get('address', ''),
            medical_notes=data.get('medical_notes', ''),
        )
        
        # Calculate and debug inventory
        updated_inventory = get_blood_inventory()
        print(f"Updated inventory: {updated_inventory}")
        
        # Return updated statistics and inventory
        response_data = {
            'success': True,
            'message': 'Donor registered successfully!',
            'statistics': get_donor_statistics(),
            'inventory': updated_inventory,
            'donor': {
                'id': donor.id,
                'full_name': donor.full_name,
                'blood_group': donor.blood_group,
                'phone': donor.phone,
                'weight': donor.weight,
                'age': donor.age,
                'donation_count': donor.donation_count,
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)

@require_http_methods(["GET"])
def get_donor_details_api(request, donor_id):
    """API endpoint to get donor details"""
    try:
        donor = Donor.objects.get(id=donor_id)
        
        donor_data = {
            'id': donor.id,
            'full_name': donor.full_name,
            'age': donor.age,
            'gender': donor.gender,
            'phone': donor.phone,
            'blood_group': donor.blood_group,
            'weight': donor.weight,
            'donation_count': donor.donation_count,
            'donation_type': donor.donation_type,
            'donation_date': donor.donation_date.strftime('%Y-%m-%d'),
            'donation_time': donor.donation_time.strftime('%H:%M'),
            'email': donor.email,
            'address': donor.address,
            'medical_notes': donor.medical_notes,
            'registered_at': donor.registered_at.isoformat(),
        }
        
        return JsonResponse({
            'success': True,
            'donor': donor_data
        })
        
    except Donor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Donor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)

@require_http_methods(["GET"])
def get_all_donors_api(request):
    """API endpoint to get all donors"""
    try:
        donors = Donor.objects.all().order_by('-registered_at')
        
        donors_data = []
        for donor in donors:
            donors_data.append({
                'id': donor.id,
                'full_name': donor.full_name,
                'age': donor.age,
                'gender': donor.gender,
                'phone': donor.phone,
                'blood_group': donor.blood_group,
                'weight': donor.weight,
                'donation_count': donor.donation_count,
                'donation_type': donor.donation_type,
                'donation_date': donor.donation_date.strftime('%Y-%m-%d'),
                'donation_time': donor.donation_time.strftime('%H:%M'),
                'email': donor.email,
                'address': donor.address,
                'medical_notes': donor.medical_notes,
                'registered_at': donor.registered_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'donors': donors_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def update_donor_api(request):
    """API endpoint to update donor details"""
    try:
        donor_id = request.POST.get('donor_id')
        donor = Donor.objects.get(id=donor_id)
        
        # Update donor fields
        donor.full_name = request.POST.get('full_name', donor.full_name)
        donor.age = int(request.POST.get('age', donor.age))
        donor.gender = request.POST.get('gender', donor.gender)
        donor.phone = request.POST.get('phone', donor.phone)
        donor.blood_group = request.POST.get('blood_group', donor.blood_group)
        donor.weight = float(request.POST.get('weight', donor.weight))
        donor.donation_count = int(request.POST.get('donation_count', donor.donation_count))
        donor.donation_type = request.POST.get('donation_type', donor.donation_type)
        donor.email = request.POST.get('email', donor.email)
        donor.address = request.POST.get('address', donor.address)
        donor.medical_notes = request.POST.get('medical_notes', donor.medical_notes)
        
        donor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Donor updated successfully!'
        })
        
    except Donor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Donor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def delete_donor_api(request):
    """API endpoint to delete a donor"""
    try:
        donor_id = request.POST.get('donor_id')
        
        if not donor_id:
            return JsonResponse({
                'success': False,
                'message': 'Donor ID is required'
            }, status=400)
        
        # Get the donor
        donor = Donor.objects.get(id=donor_id)
        donor_name = donor.full_name
        
        # Delete the donor
        donor.delete()
        
        # Return updated statistics and inventory
        return JsonResponse({
            'success': True,
            'message': f'Donor {donor_name} deleted successfully!',
            'statistics': get_donor_statistics(),
            'inventory': get_blood_inventory(),
        })
        
    except Donor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Donor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def add_transfer_api(request):
    """API endpoint to add a new blood transfer"""
    try:
        data = request.POST
        blood_type = data.get('blood_type')
        units_requested = int(data.get('units'))
        
        # Check available inventory
        inventory = get_blood_inventory()
        available_units = inventory.get(blood_type, 0)
        
        if units_requested > available_units:
            return JsonResponse({
                'success': False,
                'message': f'Insufficient {blood_type} units. Available: {available_units}, Requested: {units_requested}'
            }, status=400)
        
        # Create new transfer
        transfer = BloodTransfer.objects.create(
            patient_name=data.get('patient_name'),
            patient_id=data.get('patient_id'),
            blood_type=data.get('blood_type'),
            units=int(data.get('units')),
            transfer_date=data.get('transfer_date'),
            transfer_time=data.get('transfer_time'),
            doctor_name=data.get('doctor_name'),
            department=data.get('department', ''),
            is_emergency=(data.get('is_emergency') == 'yes'),
            notes=data.get('notes', ''),
        )
        
        # Get updated blood flow totals
        blood_flow_totals = get_blood_flow_totals()
        
        return JsonResponse({
            'success': True,
            'message': 'Blood transfer recorded successfully!',
            'transfer': {
                'id': transfer.id,
                'patient_name': transfer.patient_name,
                'patient_id': transfer.patient_id,
                'blood_type': transfer.blood_type,
                'units': transfer.units,
                'transfer_date': str(transfer.transfer_date),
                'transfer_time': str(transfer.transfer_time)[:5],  # Get HH:MM format
                'doctor_name': transfer.doctor_name,
                'department': transfer.department,
                'is_emergency': 'yes' if transfer.is_emergency else 'no',
                'notes': transfer.notes,
            },
            'inventory': get_blood_inventory(),
            'blood_flow_totals': blood_flow_totals,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)

@require_http_methods(["GET"])
def get_transfers_api(request):
    """API endpoint to get all blood transfers"""
    try:
        transfers = BloodTransfer.objects.all().order_by('-created_at')
        
        transfers_data = []
        for transfer in transfers:
            transfers_data.append({
                'id': transfer.id,
                'patient_name': transfer.patient_name,
                'patient_id': transfer.patient_id,
                'blood_type': transfer.blood_type,
                'units': transfer.units,
                'transfer_date': str(transfer.transfer_date),
                'transfer_time': str(transfer.transfer_time)[:5],  # Get HH:MM format
                'doctor_name': transfer.doctor_name,
                'department': transfer.department,
                'is_emergency': 'yes' if transfer.is_emergency else 'no',
                'notes': transfer.notes,
            })
        
        return JsonResponse({
            'success': True,
            'transfers': transfers_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)

@login_required
def donors_list(request):
    """View to display all donors with search and pagination"""
    search_query = request.GET.get('search', '')
    
    # Get all donors
    donors = Donor.objects.all().order_by('-registered_at')
    
    # Apply search filter if provided
    if search_query:
        donors = donors.filter(
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(blood_group__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(donors, 20)  # Show 20 donors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_donors': donors.count(),
        'page_title': 'All Donors - Blood Bank Management'
    }
    
    return render(request, 'blood_bank/donors_list.html', context)

@login_required
def transfers_list(request):
    """View to display all blood transfers with pagination"""
    search_query = request.GET.get('search', '').strip()

    transfers = BloodTransfer.objects.all().order_by('-created_at')

    if search_query:
        transfers = transfers.filter(
            Q(patient_name__icontains=search_query) |
            Q(doctor_name__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(blood_type__icontains=search_query)
        )

    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_transfers': transfers.count(),
        'page_title': 'All Blood Transfers',
        'active_page': 'blood_transfer',
    }
    return render(request, 'blood_bank/transfers_list.html', context)
