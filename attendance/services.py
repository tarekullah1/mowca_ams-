import os
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Make sure to reload the latest env vars
load_dotenv(override=True)

logger = logging.getLogger(__name__)

BIOTIME_SERVER_URL = os.getenv('BIOTIME_SERVER_URL', 'http://127.0.0.1:8090')
BIOTIME_USERNAME = os.getenv('BIOTIME_USERNAME', '')
BIOTIME_PASSWORD = os.getenv('BIOTIME_PASSWORD', '')

# Timeouts: (connect_timeout, read_timeout) in seconds
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30

# Circuit-breaker: suppress repeated error logs if server is unreachable
_server_unreachable = False
_last_unreachable_log = None
_UNREACHABLE_LOG_INTERVAL = timedelta(minutes=5)  # only log once every 5 mins

# Simple in-memory cache for the token
_cached_token = None


def _log_connection_error(context: str, exc: Exception):
    """Log connection errors with rate-limiting to avoid log spam in production."""
    global _server_unreachable, _last_unreachable_log
    now = datetime.now()
    if (
        not _server_unreachable
        or _last_unreachable_log is None
        or (now - _last_unreachable_log) >= _UNREACHABLE_LOG_INTERVAL
    ):
        logger.error(
            "[BioTime] %s — BioTime server unreachable at %s. "
            "If running in production, ensure BIOTIME_SERVER_URL points to a "
            "publicly accessible host (not a local LAN IP). Error: %s",
            context,
            BIOTIME_SERVER_URL,
            exc,
        )
        _server_unreachable = True
        _last_unreachable_log = now


def _make_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_token():
    global _cached_token, _server_unreachable
    if _cached_token:
        return _cached_token

    url = f"{BIOTIME_SERVER_URL}/jwt-api-token-auth/"
    try:
        session = _make_session()
        response = session.post(
            url,
            json={"username": BIOTIME_USERNAME, "password": BIOTIME_PASSWORD},
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
        if response.status_code == 200:
            data = response.json()
            _cached_token = data.get("token")
            _server_unreachable = False  # reset circuit-breaker on success
            return _cached_token
        else:
            logger.warning("[BioTime] Token request returned HTTP %s", response.status_code)
    except requests.exceptions.ConnectionError as e:
        _log_connection_error("get_token", e)
    except requests.exceptions.Timeout as e:
        _log_connection_error("get_token (timeout)", e)
    except Exception as e:
        logger.error("[BioTime] Unexpected error in get_token: %s", e)
    return None


def get_headers():
    token = get_token()
    return {
        "Content-Type": "application/json",
        "Authorization": f"JWT {token}" if token else "",
    }


def _invalidate_token():
    global _cached_token
    _cached_token = None


def get_all_employees():
    """Fetch all employees from BioTime 9.5."""
    url = f"{BIOTIME_SERVER_URL}/personnel/api/employees/"
    params = {"page_size": 1000}
    try:
        session = _make_session()
        response = session.get(
            url, headers=get_headers(), params=params,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
        if response.status_code == 200:
            _server_unreachable = False
            return response.json().get("data", [])
        elif response.status_code == 401:
            # Token expired — clear cache and retry once
            _invalidate_token()
            response = session.get(
                url, headers=get_headers(), params=params,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if response.status_code == 200:
                return response.json().get("data", [])
        else:
            logger.warning("[BioTime] get_all_employees returned HTTP %s", response.status_code)
    except requests.exceptions.ConnectionError as e:
        _log_connection_error("get_all_employees", e)
    except requests.exceptions.Timeout as e:
        _log_connection_error("get_all_employees (timeout)", e)
    except requests.exceptions.RequestException as e:
        logger.error("[BioTime] Error fetching employees: %s", e)
    return []


def get_today_transactions():
    """Fetch all transactions for today."""
    url = f"{BIOTIME_SERVER_URL}/iclock/api/transactions/"
    today_str = datetime.now().strftime("%Y-%m-%d")
    params = {
        "start_time": f"{today_str} 00:00:00",
        "end_time": f"{today_str} 23:59:59",
        "page_size": 5000,
    }
    try:
        session = _make_session()
        response = session.get(
            url, headers=get_headers(), params=params,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
        if response.status_code == 200:
            _server_unreachable = False
            return response.json().get("data", [])
        elif response.status_code == 401:
            _invalidate_token()
            response = session.get(
                url, headers=get_headers(), params=params,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if response.status_code == 200:
                return response.json().get("data", [])
        else:
            logger.warning("[BioTime] get_today_transactions returned HTTP %s", response.status_code)
    except requests.exceptions.ConnectionError as e:
        _log_connection_error("get_today_transactions", e)
    except requests.exceptions.Timeout as e:
        _log_connection_error("get_today_transactions (timeout)", e)
    except requests.exceptions.RequestException as e:
        logger.error("[BioTime] Error fetching transactions: %s", e)
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
