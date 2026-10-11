import os
import re
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
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
    Spawns the sync in a background thread so the HTTP response returns immediately,
    preventing 500 Internal Server Errors caused by web server (Gunicorn) timeouts.
    Call: GET /manage/force-sync/?token=<ADMIN_SECRET>
    """
    if not _check_admin_secret(request):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        import threading
        from .scheduler import sync_biotime_data_force

        sync_thread = threading.Thread(target=sync_biotime_data_force, daemon=True)
        sync_thread.start()
        return JsonResponse({
            'status': 'ok',
            'message': 'Force sync started in background successfully. Check your API logs or endpoints in a moment.'
        })
    except Exception as e:
        logger.exception('admin_force_sync_view error')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def admin_cleanup_names_view(request):
    """
    Secret endpoint to clean up 'None' / 'Of' junk suffixes in person_name fields.
    Call: GET /manage/cleanup-names/?token=<ADMIN_SECRET>
    """
    if not _check_admin_secret(request):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    # Matches one or more occurrences of 'Of', 'None', or 'Null' at the end of the name
    pattern = re.compile(r'(\s+\b(None|Of|Null)\b)+\s*$', re.IGNORECASE)
    results = {}

    for Model, label in [(EmployeeEnrollment, 'EmployeeEnrollment'), (AttendanceLog, 'AttendanceLog')]:
        qs = Model.objects.filter(
            Q(person_name__icontains='None') |
            Q(person_name__iendswith='Of') |
            Q(person_name__icontains=' Of ') |
            Q(person_name__icontains='Null')
        )
        count = 0
        for obj in qs:
            original = obj.person_name or ''
            cleaned = pattern.sub('', original).strip()
            # Also collapse any duplicate internal spaces
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if cleaned and cleaned != original:
                obj.person_name = cleaned
                obj.save(update_fields=['person_name'])
                count += 1
        results[label] = f'{count} records fixed'

    return JsonResponse({'status': 'ok', 'results': results})
