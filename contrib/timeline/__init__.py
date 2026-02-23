"""
Guestman Timeline - Customer interaction history.

Records every meaningful interaction: orders, contacts, notes, system events.
Provides a unified chronological view per customer — essential for CRM.

Usage:
    INSTALLED_APPS = [
        ...
        "guestman",
        "guestman.contrib.timeline",
    ]

    from guestman.contrib.timeline import TimelineService

    TimelineService.log_event(customer_code, "order", "Pedido #123 confirmado")
    events = TimelineService.get_timeline(customer_code)
"""


def __getattr__(name):
    if name == "TimelineService":
        from guestman.contrib.timeline.service import TimelineService

        return TimelineService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["TimelineService"]
