"""Management command to cleanup old processed events."""

from django.core.management.base import BaseCommand

from guestman.models import ProcessedEvent


class Command(BaseCommand):
    help = "Remove processed events older than EVENT_CLEANUP_DAYS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Override EVENT_CLEANUP_DAYS setting",
        )

    def handle(self, *args, **options):
        deleted_count, _ = ProcessedEvent.cleanup_old_events(days=options["days"])
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} old processed events.")
        )
