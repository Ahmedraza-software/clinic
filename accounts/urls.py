from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views
from .views_auth import custom_login, custom_logout

# Password reset email subjects and messages
password_reset_subjects = {
    'password_reset_subject': 'password_reset_subject.txt',
    'password_reset_email': 'registration/password_reset_email.html',
    'password_reset_done': 'registration/password_reset_done.html',
    'password_reset_confirm': 'registration/password_reset_confirm.html',
    'password_reset_complete': 'registration/password_reset_complete.html',
}

password_reset_context = {
    'email_template_name': 'registration/password_reset_email.html',
    'subject_template_name': 'registration/password_reset_subject.txt',
    'html_email_template_name': 'registration/password_reset_email.html',
    'extra_email_context': {
        'site_name': 'Clinic Management System',
    },
}

urlpatterns = [
    # Authentication URLs
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    
    # Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url=reverse_lazy('password_reset_done')
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset/confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ), 
         name='password_reset_confirm'),
    
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/update-basic/', views.update_profile_basic, name='update_profile_basic'),
    path('change-password/', views.change_password, name='change_password'),
]
