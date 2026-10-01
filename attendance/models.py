from django.db import models

class EmployeeEnrollment(models.Model):
    person_id = models.CharField(max_length=100, unique=True, db_index=True)
    person_name = models.CharField(max_length=255)
    department = models.CharField(max_length=255, null=True, blank=True)
    enrollment_status = models.CharField(max_length=100, null=True, blank=True)
    enrollment_date_time = models.DateTimeField(null=True, blank=True)
    device_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.person_name} ({self.person_id})"

class AccessAllocation(models.Model):
    person_id = models.CharField(max_length=100, db_index=True)
    person_name = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255)
    allocation_status = models.CharField(max_length=50) # Allocate / Revoke
    effective_from = models.DateTimeField(null=True, blank=True)
    effective_to = models.DateTimeField(null=True, blank=True)
    access_group = models.CharField(max_length=255, null=True, blank=True)
    allocation_date_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.allocation_status} - {self.person_name}"

class AttendanceLog(models.Model):
    log_id = models.CharField(max_length=100, unique=True, db_index=True)
    person_id = models.CharField(max_length=100, db_index=True)
    person_name = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    event_date = models.DateField()
    event_time = models.TimeField()
    event_type = models.CharField(max_length=100) # Check-in / Check-out / Access Granted
    verification_method = models.CharField(max_length=100) # Face / Card / Fingerprint

    def __str__(self):
        return f"{self.person_name} - {self.event_date} {self.event_time}"
