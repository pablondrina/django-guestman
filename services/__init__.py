"""Guestman services (CORE only).

CORE services are exported here. Contrib services are in their respective modules:
- guestman.contrib.preferences: PreferenceService
- guestman.contrib.insights: InsightService
- guestman.contrib.identifiers: IdentifierService
"""

from guestman.services import customer
from guestman.services import address

__all__ = ["customer", "address"]
