"""Guestman protocols."""

from guestman.protocols.customer import (
    CustomerBackend,
    AddressInfo,
    CustomerInfo,
    CustomerContext,
    CustomerValidationResult,
)
from guestman.protocols.orders import (
    OrderHistoryBackend,
    OrderSummary,
    OrderStats,
)

__all__ = [
    # Customer
    "CustomerBackend",
    "AddressInfo",
    "CustomerInfo",
    "CustomerContext",
    "CustomerValidationResult",
    # Orders
    "OrderHistoryBackend",
    "OrderSummary",
    "OrderStats",
]
