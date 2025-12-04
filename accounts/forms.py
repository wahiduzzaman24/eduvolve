from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    """User registration form"""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit role choices to exclude ADMIN
        self.fields['role'].choices = [
            (User.Role.INSTRUCTOR, 'Instructor'),
            (User.Role.STUDENT, 'Student'),
        ]
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class UserUpdateForm(forms.ModelForm):
    """User update form"""

    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class ProfileUpdateForm(forms.ModelForm):
    """Profile update form"""

    class Meta:
        model = User
        fields = ['bio', 'profile_picture', 'phone', 'date_of_birth']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'profile_picture':
                self.fields[field].widget.attrs.update(
                    {'class': 'form-control'})
