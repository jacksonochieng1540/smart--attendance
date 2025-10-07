# attendance/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Department, Employee, AttendanceRecord, LeaveRequest, AttendanceSettings

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'employee_id', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'employee_id', 'phone', 'profile_image')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'employee_id', 'phone')}),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Department Admin"""
    list_display = ['name', 'employee_count', 'created_at']
    search_fields = ['name']
    
    def employee_count(self, obj):
        return obj.employee_set.count()
    employee_count.short_description = 'Total Employees'

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Employee Admin"""
    list_display = ['get_full_name', 'employee_id', 'department', 'position', 'fingerprint_status', 'qr_status', 'is_active', 'date_joined']
    list_filter = ['department', 'is_active', 'fingerprint_enrolled', 'date_joined']
    search_fields = ['user__first_name', 'user__last_name', 'user__employee_id', 'position']
    readonly_fields = ['qr_code_preview', 'date_joined']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('user', 'department', 'position', 'is_active')
        }),
        ('Authentication Methods', {
            'fields': ('qr_code', 'qr_code_preview', 'qr_code_data', 'fingerprint_enrolled', 'fingerprint_data')
        }),
        ('Metadata', {
            'fields': ('date_joined',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Employee Name'
    
    def employee_id(self, obj):
        return obj.user.employee_id
    employee_id.short_description = 'Employee ID'
    
    def fingerprint_status(self, obj):
        if obj.fingerprint_enrolled:
            return format_html('<span style="color: green;">✓ Enrolled</span>')
        return format_html('<span style="color: orange;">⚠ Not Enrolled</span>')
    fingerprint_status.short_description = 'Fingerprint'
    
    def qr_status(self, obj):
        if obj.qr_code:
            return format_html('<span style="color: green;">✓ Generated</span>')
        return format_html('<span style="color: red;">✗ Not Generated</span>')
    qr_status.short_description = 'QR Code'
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="150" height="150" />', obj.qr_code.url)
        return "No QR Code"
    qr_code_preview.short_description = 'QR Code Preview'

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Attendance Record Admin"""
    list_display = ['employee_name', 'employee_id', 'date', 'check_in', 'check_out', 'working_hours', 'status_badge', 'verification_method']
    list_filter = ['status', 'verification_method', 'date', 'employee__department']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__user__employee_id']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'working_hours']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'date')
        }),
        ('Time Information', {
            'fields': ('check_in', 'check_out', 'working_hours')
        }),
        ('Status & Verification', {
            'fields': ('status', 'verification_method', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def employee_name(self, obj):
        return obj.employee.user.get_full_name()
    employee_name.short_description = 'Employee'
    
    def employee_id(self, obj):
        return obj.employee.user.employee_id
    employee_id.short_description = 'Employee ID'
    
    def status_badge(self, obj):
        colors = {
            'present': 'green',
            'late': 'orange',
            'absent': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['calculate_hours', 'mark_as_present', 'mark_as_late']
    
    def calculate_hours(self, request, queryset):
        updated = 0
        for record in queryset:
            if record.check_in and record.check_out:
                record.calculate_working_hours()
                record.save()
                updated += 1
        self.message_user(request, f'{updated} records updated with working hours.')
    calculate_hours.short_description = 'Calculate working hours'
    
    def mark_as_present(self, request, queryset):
        queryset.update(status='present')
        self.message_user(request, f'{queryset.count()} records marked as present.')
    mark_as_present.short_description = 'Mark as present'
    
    def mark_as_late(self, request, queryset):
        queryset.update(status='late')
        self.message_user(request, f'{queryset.count()} records marked as late.')
    mark_as_late.short_description = 'Mark as late'

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    """Leave Request Admin"""
    list_display = ['employee_name', 'leave_type', 'start_date', 'end_date', 'status_badge', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date', 'end_date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Employee & Leave Type', {
            'fields': ('employee', 'leave_type')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date')
        }),
        ('Details', {
            'fields': ('reason', 'status', 'approved_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def employee_name(self, obj):
        return obj.employee.user.get_full_name()
    employee_name.short_description = 'Employee'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['approve_leave', 'reject_leave']
    
    def approve_leave(self, request, queryset):
        queryset.update(status='approved', approved_by=request.user)
        self.message_user(request, f'{queryset.count()} leave requests approved.')
    approve_leave.short_description = 'Approve selected leave requests'
    
    def reject_leave(self, request, queryset):
        queryset.update(status='rejected', approved_by=request.user)
        self.message_user(request, f'{queryset.count()} leave requests rejected.')
    reject_leave.short_description = 'Reject selected leave requests'

@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    """Attendance Settings Admin"""
    list_display = ['expected_check_in_time', 'expected_check_out_time', 'grace_period_minutes', 'require_fingerprint', 'require_qr_code']
    
    fieldsets = (
        ('Expected Times', {
            'fields': ('expected_check_in_time', 'expected_check_out_time', 'grace_period_minutes')
        }),
        ('Authentication Requirements', {
            'fields': ('require_fingerprint', 'require_qr_code', 'allow_manual_entry')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return not AttendanceSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of settings
        return False