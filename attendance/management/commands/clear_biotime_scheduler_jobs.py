from django.core.management.base import BaseCommand

from attendance.scheduler import clear_stale_sync_jobs


class Command(BaseCommand):
    help = 'Delete persisted APScheduler jobs for the BioTime sync.'

    def handle(self, *args, **options):
        deleted_count = clear_stale_sync_jobs()
        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {deleted_count} persisted BioTime scheduler job(s).'
            )
        )
