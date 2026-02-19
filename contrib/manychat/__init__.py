"""
Guestman Manychat - Manychat integration for customer management.

This contrib module provides Manychat-specific fields and sync functionality.

Usage:
    INSTALLED_APPS = [
        ...
        "guestman",
        "guestman.contrib.identifiers",  # Required
        "guestman.contrib.manychat",
    ]

    from guestman.contrib.manychat import ManychatService

    customer = ManychatService.sync_subscriber(subscriber_data)
"""

default_app_config = "guestman.contrib.manychat.apps.ManychatConfig"
