from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.template.loader import select_template
import json
from .forms import CustomUserCreationForm, CustomUserChangeForm

@csrf_exempt
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Since we're using email as the username field
            user.username = form.cleaned_data['email']
            user.save()
            
            # Get the channel layer
            channel_layer = get_channel_layer()
            
            # Prepare patient data for WebSocket
            patient_data = {
                'id': user.id,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'email': user.email or '',
                'last_visit': 'Just now',
                'status': 'Active',
                'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
                'initials': f"{(user.first_name[0] if user.first_name else '')}{(user.last_name[0] if user.last_name else '')}" or 'P'
            }
            
            # Send WebSocket message
            async_to_sync(channel_layer.group_send)(
                'dashboard_updates',
                {
                    'type': 'patient.update',
                    'patient': patient_data
                }
            )
            
            # Log the user in after registration
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to the clinic management system.')
                return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    # Try accounts/profile.html first, then fallback to profile.html at root templates
    tmpl = select_template(['accounts/profile.html', 'profile.html'])
    return render(request, tmpl.template.name)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(
            request.POST, 
            request.FILES, 
            instance=request.user
        )
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def update_profile_basic(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    email = (data.get('email') or '').strip().lower()

    if not email:
        return JsonResponse({'success': False, 'error': 'Email is required'}, status=400)

    # Validate email uniqueness excluding current user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
        return JsonResponse({'success': False, 'error': 'This email is already in use'}, status=400)

    # Update user
    user = request.user
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    # Keep username aligned with email if applicable
    if hasattr(user, 'USERNAME_FIELD') and getattr(user, 'USERNAME_FIELD', '') == 'email':
        # No separate username field in our CustomUser, but keep compatibility
        pass

    user.save()

    return JsonResponse({
        'success': True,
        'data': {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip()
        }
    })
