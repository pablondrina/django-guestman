"""
Guestman Insights - Customer analytics and RFM segmentation.

This contrib module provides CustomerInsight for calculated metrics,
RFM scoring, and churn prediction.

Usage:
    INSTALLED_APPS = [
        ...
        "guestman",
        "guestman.contrib.insights",
    ]

    from guestman.contrib.insights import InsightService

    insight = InsightService.get_insight(customer_code)
    InsightService.recalculate(customer_code)
"""


def __getattr__(name):
    if name == "InsightService":
        from guestman.contrib.insights.service import InsightService

        return InsightService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["InsightService"]
