# attendance/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Employee, AttendanceRecord, LeaveRequest, Department

class CustomUserCreationForm(UserCreationForm):
    """Enhanced User Creation Form with additional fields"""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        })
    )
    employee_id = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Employee ID'
        })
    )
    position = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Position/Job Title'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with enhanced styling"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with enhanced styling"""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })
    )

class UserUpdateForm(forms.ModelForm):
    """Form for updating user information"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class EmployeeUpdateForm(forms.ModelForm):
    """Form for updating employee profile"""
    class Meta:
        model = Employee
        fields = ['phone_number', 'department', 'position', 'employee_id']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EmployeeForm(forms.ModelForm):
    """Form for creating/editing employees by admin"""
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Leave empty to keep current password"
    )

    class Meta:
        model = Employee
        fields = ['department', 'position', 'employee_id', 'phone_number']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username
            self.fields['password'].required = False

    def save(self, commit=True):
        employee = super().save(commit=False)
        
        if not employee.user_id:
            # Create new user
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=self.cleaned_data['password'] or 'defaultpassword123'
            )
            employee.user = user
        else:
            # Update existing user
            user = employee.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.username = self.cleaned_data['username']
            
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
            
            user.save()
        
        if commit:
            employee.save()
        
        return employee

class CheckInForm(forms.Form):
    """Form for QR code check-in"""
    qr_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

class CheckOutForm(forms.Form):
    """Form for check-out"""
    employee_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Employee ID'
        })
    )

class FingerprintCheckInForm(forms.Form):
    """Form for fingerprint check-in"""
    employee_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Employee ID'
        })
    )
    fingerprint_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

class LeaveRequestForm(forms.ModelForm):
    """Form for leave requests"""
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide a reason for your leave request...'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be after start date')
        
        return cleaned_data

class AttendanceRecordForm(forms.ModelForm):
    """Form for manual attendance entry"""
    class Meta:
        model = AttendanceRecord
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'check_in': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'check_out': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
        }

class DepartmentForm(forms.ModelForm):
    """Form for creating/editing departments"""
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Department description...'
            }),
        }

class PasswordResetRequestForm(forms.Form):
    """Form for password reset request"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

class ProfilePictureForm(forms.ModelForm):
    """Form for updating profile picture"""
    class Meta:
        model = Employee
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

class BulkEmployeeUploadForm(forms.Form):
    """Form for bulk employee upload via CSV"""
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="Upload a CSV file with columns: first_name, last_name, email, username, employee_id, department, position"
    )

class AttendanceSettingsForm(forms.ModelForm):
    """Form for attendance settings"""
    class Meta:
        model = Employee  # This should be your settings model
        fields = ['working_hours_start', 'working_hours_end', 'late_threshold']
        widgets = {
            'working_hours_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'working_hours_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'late_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 120,
                'step': 1
            }),
        }