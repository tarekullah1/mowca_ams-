import os
import sys

from django.apps import AppConfig


COMMANDS_WITHOUT_SCHEDULER = {
    'check',
    'collectstatic',
    'createsuperuser',
    'dbshell',
    'flush',
    'makemigrations',
    'migrate',
    'shell',
    'showmigrations',
    'test',
}


def _env_flag_enabled(name):
    return os.environ.get(name, '').strip().lower() in {'1', 'true', 'yes', 'on'}


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'

    def ready(self):
        if not self._should_start_scheduler():
            return

        from . import scheduler
        scheduler.start_scheduler()

    def _should_start_scheduler(self):
        if os.environ.get('DISABLE_ATTENDANCE_SCHEDULER') == '1':
            return False

        if not (
            _env_flag_enabled('ATTENDANCE_SCHEDULER_AUTOSTART')
            or _env_flag_enabled('BIOTIME_SCHEDULER_AUTOSTART')
        ):
            return False

        command_args = set(sys.argv[1:])
        if command_args & COMMANDS_WITHOUT_SCHEDULER:
            return False

        if os.path.basename(sys.argv[0]) == 'manage.py':
            if 'runserver' not in command_args:
                return False

            # With Django's autoreloader, only the child process should run jobs.
            if '--noreload' not in command_args and os.environ.get('RUN_MAIN') != 'true':
                return False

        return True
