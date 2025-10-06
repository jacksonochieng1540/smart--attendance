from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Attendance Records
    path('records/', views.attendance_records, name='records'),
    path('reports/', views.reports, name='reports'),
    
    # Employees
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    
    # Check-in/Check-out
    path('check-in/qr/', views.check_in_qr, name='check_in_qr'),
    path('check-in/fingerprint/', views.check_in_fingerprint, name='check_in_fingerprint'),
    path('check-out/', views.check_out, name='check_out'),
    
    # Fingerprint Management
    path('employees/<int:pk>/enroll-fingerprint/', views.enroll_fingerprint, name='enroll_fingerprint'),
]