"""Omniman OrderHistoryBackend adapter."""

from guestman.protocols.orders import OrderHistoryBackend, OrderSummary, OrderStats


class OmnimanOrderHistoryBackend:
    """
    Adapter that implements OrderHistoryBackend by querying Omniman.

    Configuration in settings.py:
        GUESTMAN = {
            "ORDER_HISTORY_BACKEND": "guestman.adapters.omniman_orders.OmnimanOrderHistoryBackend",
        }
    """

    def get_customer_orders(
        self,
        customer_code: str,
        limit: int = 10,
    ) -> list[OrderSummary]:
        """Return last orders for customer from Omniman."""
        # Late import to avoid circular dependency
        try:
            from omniman.models import Order
        except ImportError:
            return []

        orders = (
            Order.objects.filter(customer_ref=customer_code)
            .select_related("channel")
            .order_by("-created_at")[:limit]
        )

        return [
            OrderSummary(
                order_ref=o.ref,
                channel_code=o.channel.code if o.channel else "",
                ordered_at=o.created_at,
                total_q=o.snapshot.get("pricing", {}).get("total_q", 0)
                if o.snapshot
                else 0,
                items_count=len(o.snapshot.get("items", [])) if o.snapshot else 0,
                status=o.status,
            )
            for o in orders
        ]

    def get_order_stats(self, customer_code: str) -> OrderStats:
        """Return aggregated order statistics from Omniman."""
        try:
            from omniman.models import Order
            from django.db.models import Count, Sum
        except ImportError:
            return OrderStats(
                total_orders=0,
                total_spent_q=0,
                first_order_at=None,
                last_order_at=None,
                average_order_q=0,
            )

        qs = Order.objects.filter(customer_ref=customer_code)

        # Basic aggregation
        stats = qs.aggregate(
            total_orders=Count("id"),
        )

        first_order = qs.order_by("created_at").first()
        last_order = qs.order_by("-created_at").first()

        total_orders = stats["total_orders"] or 0

        # Calculate total spent from snapshots
        total_spent = 0
        for order in qs.only("snapshot"):
            if order.snapshot:
                total_spent += order.snapshot.get("pricing", {}).get("total_q", 0)

        return OrderStats(
            total_orders=total_orders,
            total_spent_q=total_spent,
            first_order_at=first_order.created_at if first_order else None,
            last_order_at=last_order.created_at if last_order else None,
            average_order_q=total_spent // total_orders if total_orders > 0 else 0,
        )
