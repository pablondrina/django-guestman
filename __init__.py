"""
Django Guestman - Customer Management.

Usage:
    from guestman import CustomerService
    from guestman.gates import Gates, GateError, GateResult

    cust = CustomerService.get("CUST-001")
    validation = CustomerService.validate("CUST-001")
    price_list = CustomerService.price_list("CUST-001")

    # Gates validation
    Gates.contact_point_uniqueness("whatsapp", "+5543999999999")
    Gates.provider_event_authenticity(body, signature, secret)
"""


def __getattr__(name):
    if name == "CustomerService":
        from guestman.service import CustomerService

        return CustomerService
    if name == "Gates":
        from guestman.gates import Gates

        return Gates
    if name == "GateError":
        from guestman.gates import GateError

        return GateError
    if name == "GateResult":
        from guestman.gates import GateResult

        return GateResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["CustomerService", "Gates", "GateError", "GateResult"]
__version__ = "0.5.0"
