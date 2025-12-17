from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def prescription_list(request):
    """List all prescriptions."""
    return render(request, 'prescriptions/list.html', {'active_page': 'prescriptions'})

@login_required
def create_prescription(request):
    """Create a new prescription."""
    return render(request, 'prescriptions/create.html', {'active_page': 'prescriptions'})

@login_required
def prescription_detail(request, pk):
    """View prescription details."""
    return render(request, 'prescriptions/detail.html', {'active_page': 'prescriptions'})

@login_required
def edit_prescription(request, pk):
    """Edit a prescription."""
    return render(request, 'prescriptions/edit.html', {'active_page': 'prescriptions'})

@login_required
def delete_prescription(request, pk):
    """Delete a prescription."""
    return render(request, 'prescriptions/delete.html', {'active_page': 'prescriptions'})
