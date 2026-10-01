from rest_framework import serializers
from .models import EmployeeEnrollment, AccessAllocation, AttendanceLog

class EmployeeEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeEnrollment
        fields = [
            'person_id',
            'person_name',
            'department',
            'enrollment_status',
            'enrollment_date_time',
            'device_id'
        ]

class AccessAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessAllocation
        fields = [
            'person_id',
            'person_name',
            'device_id',
            'allocation_status',
            'effective_from',
            'effective_to',
            'access_group',
            'allocation_date_time'
        ]

class AttendanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceLog
        fields = [
            'log_id',
            'person_id',
            'person_name',
            'device_id',
            'event_date',
            'event_time',
            'event_type',
            'verification_method'
        ]
