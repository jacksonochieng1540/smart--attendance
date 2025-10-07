from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Authentication
    path('register/', views.register, name='register'),
    
    # Attendance
    path('check-in/qr/', views.check_in_qr, name='check_in_qr'),
    path('check-in/fingerprint/', views.check_in_fingerprint, name='check_in_fingerprint'),
    path('check-out/', views.check_out, name='check_out'),
    
    # Employees
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/enroll-fingerprint/', views.enroll_fingerprint, name='enroll_fingerprint'),
    
    # Records & Reports
    path('attendance-records/', views.attendance_records, name='attendance_records'),
    path('reports/', views.reports, name='reports'),
    
    # Leave Management
    path('leave/request/', views.leave_request, name='leave_request'),
    path('leave/pending/', views.pending_leave_requests, name='pending_leave_requests'),
    path('leave/approve/<int:pk>/', views.approve_leave_request, name='approve_leave_request'),
    path('leave/reject/<int:pk>/', views.reject_leave_request, name='reject_leave_request'),
]