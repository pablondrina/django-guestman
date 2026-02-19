"""
ProcessedEvent model for replay protection (G5).

Stores processed webhook event nonces to prevent replay attacks
in distributed/multi-server environments.
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone


class ProcessedEvent(models.Model):
    """
    Tracks processed webhook events for replay protection (G5).

    This model stores nonces/event IDs to prevent the same event
    from being processed twice in a distributed environment.
    """

    nonce = models.CharField(max_length=255, unique=True, db_index=True)
    provider = models.CharField(max_length=50, db_index=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "guestman_processed_event"
        verbose_name = "processed event"
        verbose_name_plural = "processed events"
        indexes = [
            models.Index(fields=["provider", "processed_at"]),
        ]

    def __str__(self):
        return f"{self.provider}:{self.nonce[:20]}"

    @classmethod
    def cleanup_old_events(cls, days: int = 7):
        """Remove events older than N days."""
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = cls.objects.filter(processed_at__lt=cutoff).delete()
        return deleted
