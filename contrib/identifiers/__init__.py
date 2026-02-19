"""
Guestman Identifiers - Multi-channel customer deduplication.

This contrib module provides CustomerIdentifier for linking multiple
channel identities (WhatsApp, Instagram, Facebook, etc.) to a single customer.

Usage:
    INSTALLED_APPS = [
        ...
        "guestman",
        "guestman.contrib.identifiers",
    ]

    from guestman.contrib.identifiers import IdentifierService

    customer = IdentifierService.find_by_identifier("whatsapp", "5511999999999")
    IdentifierService.add_identifier(customer_code, "instagram", "username")
"""


def __getattr__(name):
    if name == "IdentifierService":
        from guestman.contrib.identifiers.service import IdentifierService

        return IdentifierService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["IdentifierService"]

default_app_config = "guestman.contrib.identifiers.apps.IdentifiersConfig"
