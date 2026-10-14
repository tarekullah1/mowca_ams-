"""
Standalone BioTime to Cloud Neon DB Sync Worker.

Can be run:
1. As a continuous background loop:
   python sync_worker.py --loop

2. As a one-shot execution (perfect for Windows Task Scheduler every 5 mins):
   python sync_worker.py --once
"""
import os
import sys
import time
import argparse
import logging
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.utils import timezone
from attendance.scheduler import _run_sync_core

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger("sync_worker")


def is_within_window():
    start_str = os.getenv('BIOTIME_SYNC_START_TIME', '06:00')
    end_str = os.getenv('BIOTIME_SYNC_END_TIME', '22:00')
    try:
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
    except ValueError:
        start_time = datetime.strptime('06:00', '%H:%M').time()
        end_time = datetime.strptime('22:00', '%H:%M').time()

    now = timezone.localtime().time()
    return start_time <= now <= end_time


def run_single_sync(force=False):
    if not force and not is_within_window():
        logger.info("Current time is outside the sync window. Skipping.")
        return

    logger.info("Starting sync from BioTime to Cloud Neon Database...")
    t0 = time.time()
    try:
        _run_sync_core()
        elapsed = time.time() - t0
        logger.info(f"Sync completed successfully in {elapsed:.2f} seconds.")
    except Exception as e:
        logger.error(f"Sync failed with error: {e}", exc_info=True)


def run_loop(interval_seconds=300):
    logger.info(f"Starting BioTime Sync Worker daemon (interval: {interval_seconds}s)...")
    while True:
        try:
            run_single_sync()
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in worker loop: {e}")

        logger.info(f"Sleeping for {interval_seconds} seconds...")
        time.sleep(interval_seconds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="BioTime to Cloud Neon Sync Worker")
    parser.add_argument('--loop', action='store_true', help="Run in a continuous loop")
    parser.add_argument('--once', action='store_true', help="Run once and exit (default)")
    parser.add_argument('--force', action='store_true', help="Bypass the time-window check")
    parser.add_argument('--interval', type=int, default=300, help="Interval in seconds for loop mode (default: 300)")

    args = parser.parse_args()

    if args.loop:
        run_loop(args.interval)
    else:
        run_single_sync(force=args.force)
