from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Employee, AttendanceRecord, Department, LeaveRequest, AttendanceSettings
from .forms import CheckInForm, CheckOutForm, EmployeeForm,PasswordChangeForm,LeaveRequestForm, CustomPasswordChangeForm, CustomUserCreationForm,EmployeeUpdateForm,UserUpdateForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import json


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Create user
                user = form.save()
                
                # Create employee profile
                employee = Employee.objects.create(
                    user=user,
                    phone_number=form.cleaned_data.get('phone', ''),
                    employee_id=form.cleaned_data['employee_id'],
                    position=form.cleaned_data['position'],
                    department_id=form.cleaned_data['department'],
                    is_active=True
                )
                
                # Log the user in
                login(request, user)
                messages.success(request, f"Account created successfully! Welcome {user.get_full_name()}")
                return redirect('attendance:dashboard')
                
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
                # Clean up if user was created but employee failed
                if User.objects.filter(username=form.cleaned_data['username']).exists():
                    User.objects.filter(username=form.cleaned_data['username']).delete()
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('attendance:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/change_password.html', {'form': form})

@login_required
def dashboard(request):
    """Main dashboard view"""
    today = timezone.now().date()
    
    total_employees = Employee.objects.filter(is_active=True).count()
    present_today = AttendanceRecord.objects.filter(
        date=today,
        status__in=['present', 'late']
    ).count()
    
    absent_today = total_employees - present_today
    late_today = AttendanceRecord.objects.filter(
        date=today,
        status='late'
    ).count()
    
  
    avg_hours = AttendanceRecord.objects.filter(
        date=today,
        working_hours__isnull=False
    ).aggregate(Avg('working_hours'))['working_hours__avg'] or 0
    
    
    recent_records = AttendanceRecord.objects.select_related(
        'employee__user', 'employee__department'
    ).filter(date=today)[:10]
    
   
    present_employee_ids = AttendanceRecord.objects.filter(
        date=today
    ).values_list('employee_id', flat=True)
    
    absent_employees = Employee.objects.filter(
        is_active=True
    ).exclude(id__in=present_employee_ids)
    
    context = {
        'total_employees': total_employees,
        'present_count': present_today,
        'absent_count': absent_today,
        'late_count': late_today,
        'avg_hours': round(avg_hours, 2),
        'recent_records': recent_records,
        'absent_employees': absent_employees,
        'today': today,
    }
    
    return render(request, 'attendance/dashboard.html', context)

@login_required
def attendance_records(request):
    """View all attendance records"""
    date_filter = request.GET.get('date', timezone.now().date())
    status_filter = request.GET.get('status', 'all')
    department_filter = request.GET.get('department', 'all')
    
    records = AttendanceRecord.objects.select_related(
        'employee__user', 'employee__department'
    ).filter(date=date_filter)
    
    if status_filter != 'all':
        records = records.filter(status=status_filter)
    
    if department_filter != 'all':
        records = records.filter(employee__department_id=department_filter)
    
    departments = Department.objects.all()
    
    context = {
        'records': records,
        'departments': departments,
        'selected_date': date_filter,
        'selected_status': status_filter,
        'selected_department': department_filter,
    }
    
    return render(request, 'attendance/records.html', context)

@login_required
def employee_list(request):
    """List all employees"""
    employees = Employee.objects.select_related(
        'user', 'department'
    ).filter(is_active=True)
    
    search = request.GET.get('search', '')
    if search:
        employees = employees.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__employee_id__icontains=search)
        )
    
    context = {
        'employees': employees,
        'search': search,
    }
    
    return render(request, 'attendance/employees.html', context)

@login_required
def employee_detail(request, pk):
    """Employee detail view"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # Get recent attendance records for display
    attendance_history = AttendanceRecord.objects.filter(
        employee=employee
    ).select_related('employee__user').order_by('-date')[:30]
    
    # Get statistics using database aggregation
    from django.db.models import Count, Q, Avg, Sum
    
    stats = AttendanceRecord.objects.filter(
        employee=employee
    ).aggregate(
        total_days=Count('id'),
        present_days=Count('id', filter=Q(status='present')),
        late_days=Count('id', filter=Q(status='late')),
        absent_days=Count('id', filter=Q(status='absent')),
        avg_hours=Avg('working_hours'),
        total_hours=Sum('working_hours')
    )
    
    # Calculate values
    total_days = stats['total_days'] or 0
    present_days = stats['present_days'] or 0
    late_days = stats['late_days'] or 0
    absent_days = stats['absent_days'] or 0
    
    # Calculate percentages
    present_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    late_percentage = (late_days / total_days * 100) if total_days > 0 else 0
    absent_percentage = (absent_days / total_days * 100) if total_days > 0 else 0
    
    context = {
        'employee': employee,
        'attendance_history': attendance_history,
        'total_days': total_days,
        'present_days': present_days,
        'late_days': late_days,
        'absent_days': absent_days,
        'present_percentage': round(present_percentage, 1),
        'late_percentage': round(late_percentage, 1),
        'absent_percentage': round(absent_percentage, 1),
        'avg_hours': round(stats['avg_hours'] or 0, 2),
        'total_hours': round(stats['total_hours'] or 0, 2),
    }
    
    return render(request, 'attendance/employee_detail.html', context)

@login_required
def check_in_qr(request):
    """QR Code check-in"""
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data')
        
        try:
            employee = Employee.objects.get(qr_code_data=qr_data)
            today = timezone.now().date()
            current_time = timezone.now().time()
            
            #
            existing = AttendanceRecord.objects.filter(
                employee=employee,
                date=today
            ).first()
            
            if existing and existing.check_in:
                messages.warning(request, 'Already checked in today!')
                return redirect('attendance:dashboard')
           
            record, created = AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'check_in': current_time,
                    'verification_method': 'qr'
                }
            )
            
            if not created:
                record.check_in = current_time
                record.verification_method = 'qr'
            
            record.determine_status()
            record.save()
            
            messages.success(request, f'Check-in successful! Status: {record.get_status_display()}')
            return redirect('attendance:dashboard')
            
        except Employee.DoesNotExist:
            messages.error(request, 'Invalid QR code!')
    
    return render(request, 'attendance/check_in_qr.html')

@login_required
def check_in_fingerprint(request):
    """Fingerprint check-in"""
    if request.method == 'POST':
        fingerprint_data = request.POST.get('fingerprint_data')
        employee_id = request.POST.get('employee_id')
        
        try:
            employee = Employee.objects.get(
                user__employee_id=employee_id,
                fingerprint_enrolled=True
            )
            

            if not fingerprint_data:
                messages.error(request, 'Fingerprint verification failed!')
                return redirect('attendance:check_in_fingerprint')
            
            today = timezone.now().date()
            current_time = timezone.now().time()
            
            existing = AttendanceRecord.objects.filter(
                employee=employee,
                date=today
            ).first()
            
            if existing and existing.check_in:
                messages.warning(request, 'Already checked in today!')
                return redirect('attendance:dashboard')
            
           
            record, created = AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'check_in': current_time,
                    'verification_method': 'fingerprint'
                }
            )
            
            if not created:
                record.check_in = current_time
                record.verification_method = 'fingerprint'
            
            record.determine_status()
            record.save()
            
            messages.success(request, f'Check-in successful! Welcome {employee.user.get_full_name()}')
            return redirect('attendance:dashboard')
            
        except Employee.DoesNotExist:
            messages.error(request, 'Employee not found or fingerprint not enrolled!')
    
    return render(request, 'attendance/check_in_fingerprint.html')

@login_required
def check_out(request):
    """Check-out view"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        
        try:
            employee = Employee.objects.get(user__employee_id=employee_id)
            today = timezone.now().date()
            current_time = timezone.now().time()
            
            record = AttendanceRecord.objects.filter(
                employee=employee,
                date=today,
                check_in__isnull=False
            ).first()
            
            if not record:
                messages.error(request, 'No check-in record found for today!')
                return redirect('attendance:check_out')
            
            if record.check_out:
                messages.warning(request, 'Already checked out today!')
                return redirect('attendance:dashboard')
            
            record.check_out = current_time
            record.calculate_working_hours()
            record.save()
            
            messages.success(request, f'Check-out successful! Working hours: {record.working_hours}')
            return redirect('attendance:dashboard')
            
        except Employee.DoesNotExist:
            messages.error(request, 'Employee not found!')
    
    return render(request, 'attendance/check_out.html')

@login_required
def reports(request):
    """Generate attendance reports"""
    start_date = request.GET.get('start_date', (timezone.now() - timedelta(days=30)).date())
    end_date = request.GET.get('end_date', timezone.now().date())
    
    records = AttendanceRecord.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('employee__user', 'employee__department')
    
   
    total_records = records.count()
    present_count = records.filter(status='present').count()
    late_count = records.filter(status='late').count()
    absent_count = records.filter(status='absent').count()
   
    dept_stats = records.values(
        'employee__department__name'
    ).annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        late=Count('id', filter=Q(status='late'))
    )
    
    context = {
        'records': records,
        'start_date': start_date,
        'end_date': end_date,
        'total_records': total_records,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'dept_stats': dept_stats,
    }
    
    return render(request, 'attendance/reports.html', context)

@login_required
def enroll_fingerprint(request, pk):
    """Enroll fingerprint for employee"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        fingerprint_data = request.POST.get('fingerprint_data')
        
        if fingerprint_data:
            employee.fingerprint_data = fingerprint_data
            employee.fingerprint_enrolled = True
            employee.save()
            
            messages.success(request, 'Fingerprint enrolled successfully!')
            return redirect('attendance:employee_detail', pk=pk)
        else:
            messages.error(request, 'Failed to capture fingerprint!')
    
    context = {'employee': employee}
    return render(request, 'attendance/enroll_fingerprint.html', context)


@login_required
def leave_request(request):
    """Handle leave requests"""
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            # Get the employee profile for the current user
            try:
                employee = Employee.objects.get(user=request.user)
                leave_request.employee = employee
                leave_request.save()
                messages.success(request, 'Leave request submitted successfully!')
                return redirect('attendance:dashboard')
            except Employee.DoesNotExist:
                messages.error(request, 'Employee profile not found!')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LeaveRequestForm()
    
    return render(request, 'attendance/leave_request.html', {'form': form})

@login_required
def pending_leave_requests(request):
    """View pending leave requests (for managers/admins)"""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('attendance:dashboard')
    
    pending_requests = LeaveRequest.objects.filter(status='pending').select_related(
        'employee__user', 'employee__department'
    )
    
    context = {
        'pending_requests': pending_requests,
    }
    return render(request, 'attendance/pending_leave_requests.html', context)

@login_required
def approve_leave_request(request, pk):
    """Approve a leave request"""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('attendance:dashboard')
    
    leave_request = get_object_or_404(LeaveRequest, pk=pk)
    leave_request.status = 'approved'
    leave_request.approved_by = request.user
    leave_request.save()
    
    messages.success(request, f'Leave request for {leave_request.employee.user.get_full_name()} has been approved.')
    return redirect('attendance:pending_leave_requests')

@login_required
def reject_leave_request(request, pk):
    """Reject a leave request"""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('attendance:dashboard')
    
    leave_request = get_object_or_404(LeaveRequest, pk=pk)
    leave_request.status = 'rejected'
    leave_request.approved_by = request.user
    leave_request.save()
    
    messages.success(request, f'Leave request for {leave_request.employee.user.get_full_name()} has been rejected.')
    return redirect('attendance:pending_leave_requests')

@login_required
def profile(request):
    """User profile view"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found!')
        return redirect('attendance:dashboard')
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        employee_form = EmployeeUpdateForm(request.POST, instance=employee)
        
        if user_form.is_valid() and employee_form.is_valid():
            user_form.save()
            employee_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('attendance:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        employee_form = EmployeeUpdateForm(instance=employee)
    
    context = {
        'user_form': user_form,
        'employee_form': employee_form,
        'employee': employee,
    }
    
    return render(request, 'attendance/profile.html', context)

@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('attendance:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'attendance/change_password.html', {'form': form})
