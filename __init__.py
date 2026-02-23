"""
Django Guestman - Customer Management.

Usage:
    from guestman.services.customer import get, validate, price_list
    from guestman.gates import Gates, GateError, GateResult

    cust = get("CUST-001")
    validation = validate("CUST-001")
    pl = price_list("CUST-001")

    # Gates validation
    Gates.contact_point_uniqueness("whatsapp", "+5543999999999")
    Gates.provider_event_authenticity(body, signature, secret)
"""


def __getattr__(name):
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


__all__ = ["Gates", "GateError", "GateResult"]
__version__ = "0.2.0"
