from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.conf import settings
from django.views.decorators.http import require_http_methods

def custom_login(request):
    # Allow logged-in users to access login page
    # if request.user.is_authenticated:
    #     return redirect(settings.LOGIN_REDIRECT_URL)
        
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # Authenticate using EmailBackend
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Set session expiry based on "Remember me"
            if not remember_me:
                # Session will expire when the user closes the browser
                request.session.set_expiry(0)
            else:
                # Session will expire after 2 weeks (in seconds)
                request.session.set_expiry(1209600)
            
            next_url = request.POST.get('next', '')
            if not next_url or next_url == 'None':
                next_url = settings.LOGIN_REDIRECT_URL
                
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
    
    # If not POST or authentication failed, show the login form
    context = {
        'next': request.GET.get('next', '')
    }
    return render(request, 'registration/login.html', context)

@require_http_methods(["GET", "POST"])
def custom_logout(request):
    """
    Custom logout view that handles both GET and POST requests.
    """
    if request.method == 'POST':
        # Only log out if the user is logged in
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, "You have been successfully logged out.")
        return redirect('home')
    else:
        # For GET requests, show a confirmation page
        return render(request, 'registration/logout_confirm.html')
