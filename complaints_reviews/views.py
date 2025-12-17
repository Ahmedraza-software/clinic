from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ComplaintReview

# Create your views here.

@login_required
def complaints_reviews_list(request):
    """List all complaints and reviews."""
    items = ComplaintReview.objects.select_related('user').all()
    context = {
        'active_page': 'complaints',
        'items': items,
    }
    return render(request, 'complaints_reviews/list.html', context)

@login_required
def create_complaint_review(request):
    """Create a new complaint or review."""
    if request.method == 'POST':
        type_val = request.POST.get('type')
        subject = request.POST.get('subject')
        details = request.POST.get('details')
        if type_val and subject and details:
            ComplaintReview.objects.create(
                user=request.user,
                type=type_val,
                subject=subject,
                details=details,
            )
            return redirect('complaints_reviews:list')
    return render(request, 'complaints_reviews/create.html', {'active_page': 'complaints'})

@login_required
def complaint_review_detail(request, pk):
    """View complaint/review details."""
    return render(request, 'complaints_reviews/detail.html', {'active_page': 'complaints'})

@login_required
def edit_complaint_review(request, pk):
    """Edit a complaint/review."""
    return render(request, 'complaints_reviews/edit.html', {'active_page': 'complaints'})

@login_required
def delete_complaint_review(request, pk):
    """Delete a complaint/review."""
    return render(request, 'complaints_reviews/delete.html', {'active_page': 'complaints'})
