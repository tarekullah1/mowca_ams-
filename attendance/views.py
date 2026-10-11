import os
import re
import logging
from django.shortcuts import render
from django.http import JsonResponse
from .services import get_attendance_summary
from .models import EmployeeEnrollment, AttendanceLog

logger = logging.getLogger(__name__)


def _check_admin_secret(request):
    """Returns True if the request carries the correct ADMIN_SECRET token."""
    secret = os.getenv('ADMIN_SECRET', '')
    if not secret:
        return False  # refuse if env var is not set
    return request.GET.get('token') == secret


def dashboard_view(request):
    """
    Renders the main dashboard page structure.
    Data is loaded asynchronously via HTMX.
    """
    return render(request, 'dashboard.html')


def dashboard_data_view(request):
    """
    HTMX endpoint that returns the data partial for the dashboard.
    """
    summary = get_attendance_summary()
    return render(request, 'partials/dashboard_data.html', {'summary': summary})


def admin_force_sync_view(request):
    """
    Secret endpoint to force a full BioTime sync bypassing the time-window.
    Call: GET /admin/force-sync/?token=<ADMIN_SECRET>
    """
    if not _check_admin_secret(request):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        from .scheduler import sync_biotime_data_force
        sync_biotime_data_force()
        return JsonResponse({'status': 'ok', 'message': 'Force sync completed successfully.'})
    except Exception as e:
        logger.exception('admin_force_sync_view error')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def admin_cleanup_names_view(request):
    """
    Secret endpoint to clean up 'None' / 'Of' junk suffixes in person_name fields.
    Call: GET /admin/cleanup-names/?token=<ADMIN_SECRET>
    """
    if not _check_admin_secret(request):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    pattern = re.compile(r'\s*(\bNone\b|\bOf\b)\s*$', re.IGNORECASE)
    results = {}

    for Model, label in [(EmployeeEnrollment, 'EmployeeEnrollment'), (AttendanceLog, 'AttendanceLog')]:
        qs = Model.objects.filter(person_name__iregex=r'\s+(None|Of)\s*$')
        count = 0
        for obj in qs:
            cleaned = pattern.sub('', obj.person_name).strip()
            if cleaned != obj.person_name:
                obj.person_name = cleaned
                obj.save(update_fields=['person_name'])
                count += 1
        results[label] = f'{count} records fixed'

    return JsonResponse({'status': 'ok', 'results': results})
