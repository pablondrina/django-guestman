"""Guestman models (CORE only).

CORE models are exported here. Contrib models are in their respective modules:
- guestman.contrib.identifiers: CustomerIdentifier, IdentifierType
- guestman.contrib.preferences: CustomerPreference, PreferenceType
- guestman.contrib.insights: CustomerInsight
"""

from guestman.models.group import CustomerGroup
from guestman.models.customer import Customer, CustomerType
from guestman.models.address import CustomerAddress, AddressLabel
from guestman.models.contact_point import ContactPoint
from guestman.models.external_identity import ExternalIdentity
from guestman.models.processed_event import ProcessedEvent

__all__ = [
    # Core models
    "CustomerGroup",
    "Customer",
    "CustomerType",
    "CustomerAddress",
    "AddressLabel",
    # Multi-channel contact management
    "ContactPoint",
    "ExternalIdentity",
    # Replay protection (G5)
    "ProcessedEvent",
]
