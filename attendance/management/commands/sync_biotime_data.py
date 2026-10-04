from django.core.management.base import BaseCommand

from attendance.scheduler import sync_data_from_biotime


class Command(BaseCommand):
    help = 'Sync employees and attendance logs from BioTime once.'

    def handle(self, *args, **options):
        self.stdout.write('Starting BioTime sync...')
        sync_data_from_biotime()
        self.stdout.write(self.style.SUCCESS('BioTime sync finished.'))
