from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        initial='patient',
        widget=forms.RadioSelect
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the username field since we're using email
        if 'username' in self.fields:
            del self.fields['username']

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Enter your password'
        }),
        min_length=4,
        help_text='',
        error_messages={
            'required': 'Please enter a password',
            'min_length': 'Password must be at least 4 characters long',
        }
    )
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'user_type']
        help_texts = {
            'password': '',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove any password validation messages
        if 'password1' in self.fields:
            self.fields['password1'].help_text = ''
            self.fields['password1'].validators = []
        if 'password2' in self.fields:
            self.fields['password2'].help_text = ''
            self.fields['password2'].validators = []
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'user_type', 'phone', 'address', 'date_of_birth', 'profile_picture')
