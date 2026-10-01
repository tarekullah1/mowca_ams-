from django.apps import AppConfig
import os

class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'

    def ready(self):
        # Prevent running scheduler twice in dev mode (reloader)
        if os.environ.get('RUN_MAIN', None) != 'true':
            from . import scheduler
            scheduler.start_scheduler()
