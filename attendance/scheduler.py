import logging
import atexit
import os
import pickle
import threading
from threading import Lock
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from django.db import DatabaseError
from django_apscheduler.models import DjangoJob
from django_apscheduler.jobstores import DjangoJobStore, register_events
from .services import get_all_employees, get_today_transactions
from .models import EmployeeEnrollment, AccessAllocation, AttendanceLog

logger = logging.getLogger(__name__)


def _get_sync_interval_seconds():
    raw_interval = os.getenv('BIOTIME_SYNC_INTERVAL_SECONDS', '60')
    try:
        interval = int(raw_interval)
    except ValueError:
        logger.warning(
            "Invalid BIOTIME_SYNC_INTERVAL_SECONDS=%r; using 60 seconds.",
            raw_interval,
        )
        return 60

    if interval < 60:
        logger.warning(
            "BIOTIME_SYNC_INTERVAL_SECONDS=%s is too low; using 60 seconds.",
            interval,
        )
        return 60

    return interval


JOB_ID = 'sync_biotime_data'
JOB_NAME = 'sync_biotime_data'
JOB_FUNC_REF = 'attendance.scheduler:sync_data_from_biotime'
SYNC_INTERVAL_SECONDS = _get_sync_interval_seconds()

_scheduler = None
_scheduler_lock = Lock()
_shutdown_registered = False


def sync_data_from_biotime():
    """
    Job that pulls data from BioTime and saves it to the local DB.
    """
    logger.info("Starting BioTime data sync...")
    try:
        # Sync Employees / Enrollments
        employees = get_all_employees()
        for emp in employees:
            person_id = str(emp.get('emp_code'))
            person_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            dept_data = emp.get('department')
            department = dept_data.get('dept_name') if isinstance(dept_data, dict) else str(dept_data)
            
            # Use app_status for enrollment status
            app_status = emp.get('app_status', 0)
            status_map = {0: "Active", 1: "Inactive"}
            enrollment_status = status_map.get(app_status, str(app_status))
            
            hire_date_str = emp.get('hire_date')
            enrollment_date = None
            if hire_date_str:
                try:
                    enrollment_date = datetime.strptime(hire_date_str, "%Y-%m-%d")
                except ValueError:
                    pass

            # Default device for now or extract from area mapping
            device_id = "Default"
            
            EmployeeEnrollment.objects.update_or_create(
                person_id=person_id,
                defaults={
                    'person_name': person_name,
                    'department': department,
                    'enrollment_status': enrollment_status,
                    'enrollment_date_time': enrollment_date,
                    'device_id': device_id
                }
            )

        # Sync Logs (Transactions)
        transactions = get_today_transactions()
        for tx in transactions:
            log_id = str(tx.get('id'))
            person_id = str(tx.get('emp_code'))
            
            # Find person_name from synced employees or just use ID
            emp_enrollment = EmployeeEnrollment.objects.filter(person_id=person_id).first()
            person_name = emp_enrollment.person_name if emp_enrollment else person_id

            device_id = tx.get('terminal_alias') or tx.get('terminal_sn') or 'Unknown'
            
            punch_time_str = tx.get('punch_time') # Format: 2019-03-04 09:50:00
            try:
                dt = datetime.strptime(punch_time_str, "%Y-%m-%d %H:%M:%S")
                event_date = dt.date()
                event_time = dt.time()
            except (ValueError, TypeError):
                continue
                
            punch_state = str(tx.get('punch_state', ''))
            state_map = {"0": "Check-in", "1": "Check-out", "2": "Break-out", "3": "Break-in", "4": "Overtime-in", "5": "Overtime-out"}
            event_type = state_map.get(punch_state, punch_state)

            verify_type = str(tx.get('verify_type', ''))
            verify_map = {"1": "Fingerprint", "15": "Face", "4": "Card"}
            verification_method = verify_map.get(verify_type, verify_type)

            AttendanceLog.objects.update_or_create(
                log_id=log_id,
                defaults={
                    'person_id': person_id,
                    'person_name': person_name,
                    'device_id': device_id,
                    'event_date': event_date,
                    'event_time': event_time,
                    'event_type': event_type,
                    'verification_method': verification_method
                }
            )
            
        logger.info("BioTime data sync completed successfully.")
    except Exception as e:
        logger.error(f"Error during BioTime data sync: {e}")


def shutdown_scheduler():
    global _scheduler

    with _scheduler_lock:
        scheduler = _scheduler
        if scheduler is None or not scheduler.running:
            _scheduler = None
            return

        try:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped.")
        except Exception as e:
            logger.warning("Error stopping scheduler: %s", e)
        finally:
            _scheduler = None


def _register_shutdown_hook():
    global _shutdown_registered

    if _shutdown_registered:
        return

    try:
        threading_atexit = getattr(threading, '_register_atexit')
    except AttributeError:
        atexit.register(shutdown_scheduler)
    else:
        threading_atexit(shutdown_scheduler)

    _shutdown_registered = True


def _delete_stale_sync_jobs():
    stale_job_ids = []

    try:
        for stored_job in DjangoJob.objects.all().only('id', 'job_state').iterator():
            if stored_job.id == JOB_ID:
                stale_job_ids.append(stored_job.id)
                continue

            try:
                job_state = pickle.loads(stored_job.job_state)
            except Exception:
                continue

            if (
                job_state.get('name') == JOB_NAME
                or job_state.get('func') == JOB_FUNC_REF
            ):
                stale_job_ids.append(stored_job.id)

        if stale_job_ids:
            deleted_count, _ = DjangoJob.objects.filter(id__in=stale_job_ids).delete()
            logger.info("Deleted %s stale BioTime scheduler job(s).", deleted_count)
    except DatabaseError:
        logger.exception("Could not clean stale BioTime scheduler jobs.")
        raise


def start_scheduler():
    global _scheduler

    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            logger.info("Scheduler already running.")
            return _scheduler

        _delete_stale_sync_jobs()

        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Keep the job id stable so persisted schedules are replaced on restart.
        scheduler.add_job(
            sync_data_from_biotime,
            'interval',
            seconds=SYNC_INTERVAL_SECONDS,
            id=JOB_ID,
            name=JOB_NAME,
            jobstore='default',
            replace_existing=True,
            max_instances=1,       # Prevent overlapping runs
            coalesce=True,         # If multiple missed, only run once
            misfire_grace_time=max(60, SYNC_INTERVAL_SECONDS),
        )
        register_events(scheduler)
        scheduler.start()

        _scheduler = scheduler
        _register_shutdown_hook()

        logger.info("Scheduler started.")
        return scheduler
