# attendance/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
import uuid

class User(AbstractUser):
    """Extended User model"""
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('employee', 'Employee'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = f"EMP{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

class Department(models.Model):
    """Department model"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Employee(models.Model):
    """Employee model with QR and fingerprint data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    position = models.CharField(max_length=100)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_code_data = models.CharField(max_length=255, unique=True, blank=True)
    fingerprint_data = models.TextField(blank=True, null=True)  # Store fingerprint template
    fingerprint_enrolled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.user.employee_id}"
    
    def generate_qr_code(self):
        """Generate QR code for employee"""
        qr_data = f"{self.user.employee_id}:{self.user.email}:{uuid.uuid4()}"
        self.qr_code_data = qr_data
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'qr_{self.user.employee_id}.png'
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()
        
    def save(self, *args, **kwargs):
        if not self.qr_code_data:
            self.generate_qr_code()
        super().save(*args, **kwargs)

class AttendanceRecord(models.Model):
    """Attendance tracking model"""
    VERIFICATION_CHOICES = (
        ('qr', 'QR Code'),
        ('fingerprint', 'Fingerprint'),
        ('manual', 'Manual'),
    )
    
    STATUS_CHOICES = (
        ('present', 'Present on time'),
        ('late', 'Late'),
        ('absent', 'Absent'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-check_in']
        unique_together = ['employee', 'date']
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.date}"
    
    def calculate_working_hours(self):
        """Calculate working hours"""
        if self.check_in and self.check_out:
            from datetime import datetime, timedelta
            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)
            
            if check_out_dt < check_in_dt:
                check_out_dt += timedelta(days=1)
            
            duration = check_out_dt - check_in_dt
            hours = duration.total_seconds() / 3600
            self.working_hours = round(hours, 2)
            return self.working_hours
        return 0
    
    def determine_status(self, expected_time="09:00"):
        """Determine if employee is late"""
        from datetime import datetime
        if self.check_in:
            expected = datetime.strptime(expected_time, "%H:%M").time()
            if self.check_in > expected:
                self.status = 'late'
            else:
                self.status = 'present'
        else:
            self.status = 'absent'

class LeaveRequest(models.Model):
    """Leave management model"""
    LEAVE_TYPES = (
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('vacation', 'Vacation'),
        ('emergency', 'Emergency'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.leave_type} ({self.start_date})"

class AttendanceSettings(models.Model):
    """System settings for attendance"""
    expected_check_in_time = models.TimeField(default="09:00")
    expected_check_out_time = models.TimeField(default="17:00")
    grace_period_minutes = models.IntegerField(default=15)
    require_fingerprint = models.BooleanField(default=True)
    require_qr_code = models.BooleanField(default=True)
    allow_manual_entry = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Attendance Settings"
    
    def __str__(self):
        return "Attendance System Settings"