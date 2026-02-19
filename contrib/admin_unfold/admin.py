"""
Guestman Admin with Unfold theme.

This module provides Unfold-styled admin classes for Guestman models.
To use, add 'guestman.contrib.admin_unfold' to INSTALLED_APPS after 'guestman'.

The admins will automatically unregister the basic admins and register
the Unfold versions.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.decorators import display

from guestman.contrib.admin_unfold.base import BaseModelAdmin, BaseTabularInline
from guestman.models import (
    Customer,
    CustomerGroup,
    CustomerAddress,
)


def _unfold_badge(text, color="base"):
    """Create Unfold badge with colored background."""
    base_classes = (
        "inline-block font-semibold h-6 leading-6 px-2 "
        "rounded-default whitespace-nowrap text-xs uppercase"
    )

    color_classes = {
        "base": "bg-base-100 text-base-700 dark:bg-base-500/20 dark:text-base-200",
        "red": "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400",
        "green": "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400",
        "yellow": "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400",
        "blue": "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400",
    }

    classes = f"{base_classes} {color_classes.get(color, color_classes['base'])}"
    return format_html('<span class="{}">{}</span>', classes, text)


# Unregister basic admins
for model in [Customer, CustomerGroup, CustomerAddress]:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass


# =============================================================================
# CUSTOMER GROUP ADMIN
# =============================================================================


@admin.register(CustomerGroup)
class CustomerGroupAdmin(BaseModelAdmin):
    list_display = [
        "code",
        "name",
        "price_list_code",
        "priority",
        "is_default_badge",
        "customer_count",
    ]
    list_filter = ["is_default"]
    search_fields = ["code", "name"]
    ordering = ["-priority", "name"]

    @display(description="Default", boolean=True)
    def is_default_badge(self, obj):
        return obj.is_default

    @display(description="Customers")
    def customer_count(self, obj):
        return obj.customers.count()


# =============================================================================
# CUSTOMER ADMIN
# =============================================================================


class CustomerAddressInline(BaseTabularInline):
    model = CustomerAddress
    extra = 0
    fields = ["label", "formatted_address", "is_default", "is_verified"]
    readonly_fields = ["is_verified"]


@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):
    list_display = [
        "code",
        "name",
        "customer_type_badge",
        "group",
        "phone",
        "orders_link",
        "is_active_badge",
    ]
    list_filter = ["customer_type", "group", "is_active"]
    search_fields = ["code", "first_name", "last_name", "document", "phone", "email"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    inlines = [CustomerAddressInline]

    fieldsets = [
        (
            "Identification",
            {
                "fields": [
                    "code",
                    "uuid",
                    "first_name",
                    "last_name",
                    "customer_type",
                    "document",
                ]
            },
        ),
        ("Contact", {"fields": ["email", "phone"]}),
        ("Segmentation", {"fields": ["group", "notes"]}),
        (
            "System",
            {
                "fields": [
                    "is_active",
                    "metadata",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "source_system",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    @display(description="Type")
    def customer_type_badge(self, obj):
        colors = {
            "individual": "blue",
            "company": "green",
        }
        color = colors.get(obj.customer_type, "base")
        return _unfold_badge(obj.get_customer_type_display(), color)

    @display(description="Active", boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active

    @display(description="Orders")
    def orders_link(self, obj):
        """Show order count with link to order list filtered by this customer."""
        try:
            from omniman.models import Order

            count = Order.objects.filter(
                handle_type="customer", handle_ref=obj.code
            ).count()
            if count == 0:
                return "-"
            url = (
                reverse("admin:omniman_order_changelist")
                + f"?handle_type=customer&handle_ref={obj.code}"
            )
            return format_html(
                '<a href="{}" class="text-primary-600 hover:text-primary-700">'
                "{} pedido{}</a>",
                url,
                count,
                "s" if count != 1 else "",
            )
        except ImportError:
            return "-"


# =============================================================================
# CUSTOMER ADDRESS ADMIN
# =============================================================================


@admin.register(CustomerAddress)
class CustomerAddressAdmin(BaseModelAdmin):
    list_display = [
        "customer",
        "label_badge",
        "formatted_address",
        "is_default_badge",
        "is_verified_badge",
    ]
    list_filter = ["label", "is_default", "is_verified"]
    search_fields = ["customer__code", "customer__first_name", "formatted_address"]
    raw_id_fields = ["customer"]

    @display(description="Label")
    def label_badge(self, obj):
        colors = {
            "home": "green",
            "work": "blue",
            "other": "base",
        }
        color = colors.get(obj.label, "base")
        return _unfold_badge(obj.get_label_display(), color)

    @display(description="Default", boolean=True)
    def is_default_badge(self, obj):
        return obj.is_default

    @display(description="Verified", boolean=True)
    def is_verified_badge(self, obj):
        return obj.is_verified
