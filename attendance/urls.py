from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard-data/', views.dashboard_data_view, name='dashboard-data'),
    
    # API Endpoints
    path('api/v1/enrollments/', api_views.EnrollmentListAPIView.as_view(), name='api-enrollments'),
    path('api/v1/allocations/', api_views.AccessAllocationListAPIView.as_view(), name='api-allocations'),
    path('api/v1/logs/', api_views.LogPullAPIView.as_view(), name='api-logs'),
]
