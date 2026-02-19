"""
Guestman public API.

CORE (essential):
    CustomerService.get(code)      - Get customer
    CustomerService.validate(code) - Validate customer
    CustomerService.price_list(code) - Get price list code

CONVENIENCE (helpers):
    CustomerService.search(...)    - Search customers
    CustomerService.groups()       - List groups
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from guestman.models import Customer, CustomerGroup

if TYPE_CHECKING:
    from guestman.models import CustomerAddress


@dataclass
class CustomerValidation:
    """Customer validation result."""

    valid: bool
    code: str
    customer_id: int | None = None
    name: str | None = None
    group_code: str | None = None
    price_list_code: str | None = None
    default_address: dict | None = None
    error_code: str | None = None
    message: str | None = None


class CustomerService:
    """
    Guestman public API.

    Uses @classmethod for extensibility (see spec 000 section 12.1).

    CORE (essential):
        get(code)        - Get customer
        get_by_uuid(uuid) - Get by UUID
        get_by_document(doc) - Get by document
        validate(code)   - Validate customer
        price_list(code) - Get price list code

    CONVENIENCE (helpers):
        search(...)      - Search customers
        groups()         - List groups
        create(...)      - Create customer
        update(...)      - Update customer
    """

    # ======================================================================
    # CORE API
    # ======================================================================

    @classmethod
    def get(cls, code: str) -> Customer | None:
        """
        Get customer by unique code.

        Args:
            code: Customer code

        Returns:
            Customer or None if not found/inactive
        """
        return cls._fetch_customer(code)

    @classmethod
    def _fetch_customer(cls, code: str) -> Customer | None:
        """Internal: fetch customer by code. Override for caching, etc."""
        try:
            return Customer.objects.select_related("group").get(
                code=code, is_active=True
            )
        except Customer.DoesNotExist:
            return None

    @classmethod
    def get_by_uuid(cls, uuid: str) -> Customer | None:
        """Get customer by UUID."""
        try:
            return Customer.objects.select_related("group").get(
                uuid=uuid, is_active=True
            )
        except Customer.DoesNotExist:
            return None

    @classmethod
    def get_by_document(cls, document: str) -> Customer | None:
        """Get customer by document (CPF/CNPJ)."""
        doc_normalized = "".join(filter(str.isdigit, document))
        try:
            return Customer.objects.select_related("group").get(
                document=doc_normalized, is_active=True
            )
        except Customer.DoesNotExist:
            return None

    @classmethod
    def get_by_phone(cls, phone: str) -> Customer | None:
        """Get customer by phone."""
        phone_normalized = "".join(filter(str.isdigit, phone))
        try:
            return Customer.objects.select_related("group").get(
                phone__contains=phone_normalized, is_active=True
            )
        except Customer.DoesNotExist:
            return None

    @classmethod
    def get_by_email(cls, email: str) -> Customer | None:
        """Get customer by email."""
        try:
            return Customer.objects.select_related("group").get(
                email__iexact=email, is_active=True
            )
        except Customer.DoesNotExist:
            return None

    @classmethod
    def validate(cls, code: str) -> CustomerValidation:
        """
        Validate customer and return complete info for Session.

        Args:
            code: Customer code

        Returns:
            CustomerValidation with all relevant info
        """
        cust = cls.get(code)

        if not cust:
            return CustomerValidation(
                valid=False,
                code=code,
                error_code="CUSTOMER_NOT_FOUND",
                message=f"Customer '{code}' not found",
            )

        default_addr = cust.default_address
        addr_dict = None
        if default_addr:
            addr_dict = {
                "label": default_addr.display_label,
                "formatted_address": default_addr.formatted_address,
                "short_address": default_addr.short_address,
                "complement": default_addr.complement,
                "latitude": (
                    float(default_addr.latitude) if default_addr.latitude else None
                ),
                "longitude": (
                    float(default_addr.longitude) if default_addr.longitude else None
                ),
            }

        return CustomerValidation(
            valid=True,
            code=code,
            customer_id=cust.id,
            name=cust.name,
            group_code=cust.group.code if cust.group else None,
            price_list_code=cust.price_list_code,
            default_address=addr_dict,
        )

    @classmethod
    def price_list(cls, code: str) -> str | None:
        """
        Return customer's price_list_code (for Offerman).

        Args:
            code: Customer code

        Returns:
            Price list code or None
        """
        cust = cls.get(code)
        if cust:
            return cust.price_list_code
        return None

    # ======================================================================
    # CONVENIENCE API
    # ======================================================================

    @classmethod
    def search(
        cls,
        query: str | None = None,
        group_code: str | None = None,
        only_active: bool = True,
        limit: int = 20,
    ) -> list[Customer]:
        """
        Search customers.

        Args:
            query: Search term (name, code, document, phone, or email)
            group_code: Filter by group code
            only_active: Only active customers
            limit: Maximum results

        Returns:
            List of Customer
        """
        from django.db.models import Q

        qs = Customer.objects.select_related("group")

        if only_active:
            qs = qs.filter(is_active=True)

        if query:
            qs = qs.filter(
                Q(code__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(document__icontains=query)
                | Q(phone__icontains=query)
                | Q(email__icontains=query)
            )

        if group_code:
            qs = qs.filter(group__code=group_code)

        return list(qs[:limit])

    @classmethod
    def groups(cls, only_active: bool = True) -> list[CustomerGroup]:
        """List all customer groups."""
        qs = CustomerGroup.objects.all()
        # CustomerGroup doesn't have is_active, so we just return all
        return list(qs.order_by("-priority", "name"))

    @classmethod
    def create(
        cls,
        code: str,
        first_name: str,
        last_name: str = "",
        customer_type: str = "individual",
        document: str = "",
        email: str = "",
        phone: str = "",
        group_code: str | None = None,
        **kwargs,
    ) -> Customer:
        """
        Create a new customer.

        Args:
            code: Unique customer code
            first_name: First name
            last_name: Last name
            customer_type: "individual" or "business"
            document: CPF/CNPJ (numbers only)
            email: Email address
            phone: Phone number
            group_code: Group code (optional)
            **kwargs: Additional fields

        Returns:
            Created Customer
        """
        group = None
        if group_code:
            try:
                group = CustomerGroup.objects.get(code=group_code)
            except CustomerGroup.DoesNotExist:
                pass

        return Customer.objects.create(
            code=code,
            first_name=first_name,
            last_name=last_name,
            customer_type=customer_type,
            document="".join(filter(str.isdigit, document)),
            email=email,
            phone=phone,
            group=group,
            **kwargs,
        )

    @classmethod
    def update(cls, code: str, **fields) -> Customer | None:
        """
        Update customer fields.

        Args:
            code: Customer code
            **fields: Fields to update

        Returns:
            Updated Customer or None if not found
        """
        cust = cls.get(code)
        if not cust:
            return None

        for key, value in fields.items():
            if hasattr(cust, key):
                setattr(cust, key, value)

        cust.save()
        return cust

    # ======================================================================
    # ADDRESS API
    # ======================================================================

    @classmethod
    def addresses(cls, code: str) -> list["CustomerAddress"]:
        """Get all addresses for a customer."""
        cust = cls.get(code)
        if not cust:
            return []
        return list(cust.addresses.all())

    @classmethod
    def default_address(cls, code: str) -> "CustomerAddress | None":
        """Get default address for a customer."""
        cust = cls.get(code)
        if not cust:
            return None
        return cust.default_address
