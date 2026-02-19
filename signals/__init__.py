"""Guestman signals."""

from django.dispatch import Signal

# Customer signals
customer_created = Signal()  # sender=Customer
customer_updated = Signal()  # sender=Customer, changes=dict
customer_deactivated = Signal()  # sender=Customer

# Order signals
order_recorded = Signal()  # sender=OrderSnapshot
insight_calculated = Signal()  # sender=CustomerInsight
