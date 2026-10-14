from django.core.management.base import BaseCommand
from attendance.scheduler import sync_biotime_data_force


class Command(BaseCommand):
    help = 'Force a full sync of employees and attendance logs from BioTime.'

    def handle(self, *args, **options):
        self.stdout.write('Starting force sync from BioTime...')
        sync_biotime_data_force()
        self.stdout.write(self.style.SUCCESS('Force sync completed successfully.'))
