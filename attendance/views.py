from django.shortcuts import render
from .services import get_attendance_summary

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
