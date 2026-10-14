from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('health/', views.health_check_view, name='health-check'),
    path('dashboard-data/', views.dashboard_data_view, name='dashboard-data'),

    # API Endpoints
    path('api/v1/enrollments/', api_views.EnrollmentListAPIView.as_view(), name='api-enrollments'),
    path('api/v1/allocations/', api_views.AccessAllocationListAPIView.as_view(), name='api-allocations'),
    path('api/v1/logs/', api_views.LogPullAPIView.as_view(), name='api-logs'),

    # Secret admin endpoints (protected by ADMIN_SECRET env var token)
    path('manage/force-sync/', views.admin_force_sync_view, name='admin-force-sync'),
    path('manage/cleanup-names/', views.admin_cleanup_names_view, name='admin-cleanup-names'),
]
