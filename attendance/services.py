import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Make sure to reload the latest env vars
load_dotenv(override=True)

BIOTIME_SERVER_URL = os.getenv('BIOTIME_SERVER_URL', 'http://127.0.0.1:8090')
BIOTIME_USERNAME = os.getenv('BIOTIME_USERNAME', '')
BIOTIME_PASSWORD = os.getenv('BIOTIME_PASSWORD', '')

# Simple in-memory cache for the token
_cached_token = None

def get_token():
    global _cached_token
    if _cached_token:
        return _cached_token
        
    url = f"{BIOTIME_SERVER_URL}/jwt-api-token-auth/"
    try:
        response = requests.post(url, json={
            "username": BIOTIME_USERNAME,
            "password": BIOTIME_PASSWORD
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            _cached_token = data.get('token')
            return _cached_token
    except Exception as e:
        print(f"Error fetching token: {e}")
    return None

def get_headers():
    token = get_token()
    return {
        "Content-Type": "application/json",
        "Authorization": f"JWT {token}" if token else ""
    }

def get_all_employees():
    """
    Fetch all employees from BioTime 9.5
    """
    url = f"{BIOTIME_SERVER_URL}/personnel/api/employees/"
    try:
        response = requests.get(url, headers=get_headers(), params={'page_size': 1000}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        elif response.status_code == 401:
            # Token expired, clear cache and retry once
            global _cached_token
            _cached_token = None
            response = requests.get(url, headers=get_headers(), params={'page_size': 1000}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching employees: {e}")
        return []

def get_today_transactions():
    """
    Fetch all transactions for today
    """
    url = f"{BIOTIME_SERVER_URL}/iclock/api/transactions/"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    start_time = f"{today_str} 00:00:00"
    end_time = f"{today_str} 23:59:59"
    
    params = {
        'start_time': start_time,
        'end_time': end_time,
        'page_size': 5000
    }
    
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        elif response.status_code == 401:
            global _cached_token
            _cached_token = None
            response = requests.get(url, headers=get_headers(), params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transactions: {e}")
        return []

from .models import EmployeeEnrollment, AttendanceLog

def get_attendance_summary():
    """
    Get the attendance summary by combining local synced employees and today's logs.
    """
    today = datetime.now().date()
    
    employees = EmployeeEnrollment.objects.all()
    transactions = AttendanceLog.objects.filter(event_date=today)
    
    present_emp_codes = set(transactions.values_list('person_id', flat=True))
            
    present_employees = []
    absent_employees = []
    
    for emp in employees:
        emp_dict = {
            'emp_code': emp.person_id,
            'first_name': emp.person_name,
            'last_name': '',
            'department': {'dept_name': emp.department}
        }
        if emp.person_id in present_emp_codes:
            present_employees.append(emp_dict)
        else:
            absent_employees.append(emp_dict)
            
    return {
        'total': employees.count(),
        'present_count': len(present_employees),
        'absent_count': len(absent_employees),
        'present_employees': present_employees,
        'absent_employees': absent_employees
    }
