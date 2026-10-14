from rest_framework import generics
from rest_framework.response import Response
from .models import EmployeeEnrollment, AccessAllocation, AttendanceLog
from .serializers import EmployeeEnrollmentSerializer, AccessAllocationSerializer, AttendanceLogSerializer

class EnrollmentListAPIView(generics.ListAPIView):
    """
    1. Enrollment API
    Returns the list of enrolled persons/employees.
    """
    queryset = EmployeeEnrollment.objects.all().order_by('-enrollment_date_time')
    serializer_class = EmployeeEnrollmentSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Wrap response in api_json_data_format format
        return Response({
            "status": "success",
            "message": "Enrollments retrieved successfully",
            "data": response.data
        })

class AccessAllocationListAPIView(generics.ListAPIView):
    """
    2. Person Allocate / Revoke API
    Returns access allocations and revocations.
    """
    queryset = AccessAllocation.objects.all().order_by('-allocation_date_time')
    serializer_class = AccessAllocationSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Allocations retrieved successfully",
            "data": response.data
        })

class LogPullAPIView(generics.ListAPIView):
    """
    3. Log Pull API
    Returns daily check-in/check-out logs for today (or specified ?date=YYYY-MM-DD).
    """
    serializer_class = AttendanceLogSerializer

    def get_queryset(self):
        from datetime import datetime
        from django.utils import timezone

        date_str = self.request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                target_date = timezone.localdate()
        else:
            target_date = timezone.localdate()

        return AttendanceLog.objects.filter(event_date=target_date).order_by('-event_time')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Logs retrieved successfully",
            "data": response.data
        })
