"""Tests for Guestman services."""

from decimal import Decimal
from datetime import timedelta

import pytest
from django.utils import timezone

# Core services
from guestman.services import customer as customer_service
from guestman.services import address as address_service

# Contrib services
from guestman.contrib.preferences import PreferenceService
from guestman.contrib.insights import InsightService
from guestman.contrib.identifiers import IdentifierService

# Contrib models
from guestman.contrib.identifiers.models import CustomerIdentifier, IdentifierType


pytestmark = pytest.mark.django_db


class TestCustomerService:
    """Tests for customer service."""

    def test_get_by_code(self, customer):
        """Test getting customer by code."""
        result = customer_service.get("CUST-001")
        assert result.code == "CUST-001"

    def test_get_nonexistent(self, db):
        """Test getting nonexistent customer."""
        result = customer_service.get("NONEXISTENT")
        assert result is None

    def test_get_by_document(self, db, group_regular):
        """Test getting customer by document."""
        from guestman.models import Customer

        cust = Customer.objects.create(
            code="DOC-TEST",
            first_name="Doc",
            document="12345678901",
            group=group_regular,
        )

        result = customer_service.get_by_document("123.456.789-01")
        assert result == cust

    def test_validate_valid_customer(self, customer, customer_address):
        """Test validating valid customer."""
        result = customer_service.validate("CUST-001")

        assert result.valid is True
        assert result.name == "John Doe"
        assert result.default_address is not None
        # Accept either English or Portuguese translation
        assert result.default_address["label"] in ("Home", "Casa")

    def test_validate_invalid_customer(self, db):
        """Test validating invalid customer."""
        result = customer_service.validate("NONEXISTENT")

        assert result.valid is False
        assert result.error_code == "CUSTOMER_NOT_FOUND"

    def test_price_list(self, customer_vip):
        """Test getting price list code."""
        result = customer_service.price_list("CUST-VIP")
        assert result == "vip"

    def test_search(self, customer, customer_vip):
        """Test search functionality."""
        results = customer_service.search("John")
        assert len(results) == 1
        assert results[0].code == "CUST-001"

    def test_create_customer(self, group_regular):
        """Test creating customer."""
        cust = customer_service.create(
            code="NEW-001",
            first_name="New",
            last_name="Customer",
            email="new@example.com",
            phone="11111111111",
        )
        assert cust.code == "NEW-001"
        assert cust.group == group_regular


class TestAddressService:
    """Tests for address service."""

    def test_addresses(self, customer, customer_address):
        """Test listing addresses."""
        result = address_service.addresses("CUST-001")
        assert len(result) == 1

    def test_default_address(self, customer, customer_address):
        """Test getting default address."""
        result = address_service.default_address("CUST-001")
        assert result == customer_address

    def test_add_address(self, customer):
        """Test adding address."""
        addr = address_service.add_address(
            "CUST-001",
            label="work",
            formatted_address="Av Work, 456",
            complement="10th floor",
        )
        assert addr.label == "work"
        assert addr.complement == "10th floor"

    def test_set_default_address(self, customer, customer_address):
        """Test setting default address."""
        new_addr = address_service.add_address(
            "CUST-001",
            label="work",
            formatted_address="Work address",
        )

        address_service.set_default_address("CUST-001", new_addr.id)
        new_addr.refresh_from_db()
        customer_address.refresh_from_db()

        assert new_addr.is_default is True
        assert customer_address.is_default is False


class TestPreferenceService:
    """Tests for preference service."""

    def test_get_preferences(self, customer, customer_preference):
        """Test listing preferences."""
        result = PreferenceService.get_preferences("CUST-001")
        assert len(result) == 1

    def test_get_preferences_dict(self, customer, customer_preference):
        """Test getting preferences by category."""
        result = PreferenceService.get_preferences_dict("CUST-001")
        assert "dietary" in result
        assert result["dietary"]["lactose_free"] is True

    def test_get_preference(self, customer, customer_preference):
        """Test getting specific preference."""
        result = PreferenceService.get_preference("CUST-001", "dietary", "lactose_free")
        assert result is True

    def test_set_preference(self, customer):
        """Test setting preference."""
        pref = PreferenceService.set_preference(
            "CUST-001",
            category="flavor",
            key="favorite_bread",
            value="croissant",
        )
        assert pref.value == "croissant"

    def test_get_restrictions(self, customer, customer_preference):
        """Test getting restrictions."""
        # customer_preference fixture already creates a restriction
        # Add another one to test listing multiple
        from guestman.contrib.preferences.models import PreferenceType
        PreferenceService.set_preference(
            "CUST-001",
            category="dietary",
            key="gluten_free",
            value=True,
            preference_type=PreferenceType.RESTRICTION,
        )
        restrictions = PreferenceService.get_restrictions("CUST-001")
        # customer_preference + gluten_free = 2 restrictions
        assert len(restrictions) == 2
        keys = {r.key for r in restrictions}
        assert "lactose_free" in keys
        assert "gluten_free" in keys


class TestInsightService:
    """Tests for insight service."""

    def test_get_insight(self, customer, customer_insight):
        """Test getting insight."""
        result = InsightService.get_insight("CUST-001")
        assert result.total_orders == 5

    def test_recalculate_no_backend(self, customer):
        """Test recalculating without backend (resets metrics)."""
        result = InsightService.recalculate("CUST-001")

        # Without an order backend, metrics should be reset to 0
        assert result.total_orders == 0
        assert result.total_spent_q == 0


class TestIdentifierService:
    """Tests for identifier service."""

    def test_find_by_identifier(self, customer):
        """Test finding by identifier."""
        CustomerIdentifier.objects.create(
            customer=customer,
            identifier_type=IdentifierType.EMAIL,
            identifier_value="john@example.com",
        )

        result = IdentifierService.find_by_identifier(IdentifierType.EMAIL, "john@example.com")
        assert result == customer

    def test_find_or_create_new(self, group_regular):
        """Test find_or_create creates new customer."""
        cust, created = IdentifierService.find_or_create_customer(
            identifier_type=IdentifierType.EMAIL,
            identifier_value="new@example.com",
            defaults={
                "first_name": "New",
                "last_name": "Person",
            },
        )

        assert created is True
        assert cust.first_name == "New"
        # Check identifier was created
        assert cust.identifiers.count() == 1

    def test_find_or_create_existing(self, customer):
        """Test find_or_create finds existing customer."""
        CustomerIdentifier.objects.create(
            customer=customer,
            identifier_type=IdentifierType.EMAIL,
            identifier_value="john@example.com",
        )

        cust, created = IdentifierService.find_or_create_customer(
            identifier_type=IdentifierType.EMAIL,
            identifier_value="john@example.com",
            defaults={"first_name": "Different"},
        )

        assert created is False
        assert cust == customer

    def test_add_identifier(self, customer):
        """Test adding identifier."""
        ident = IdentifierService.add_identifier(
            customer_code="CUST-001",
            identifier_type=IdentifierType.INSTAGRAM,
            identifier_value="@johndoe",
        )
        assert ident.identifier_value == "@johndoe"
        assert ident.customer == customer

    def test_get_identifiers(self, customer):
        """Test getting all identifiers for customer."""
        CustomerIdentifier.objects.create(
            customer=customer,
            identifier_type=IdentifierType.EMAIL,
            identifier_value="john@example.com",
        )
        CustomerIdentifier.objects.create(
            customer=customer,
            identifier_type=IdentifierType.PHONE,
            identifier_value="5511999999999",
        )

        identifiers = IdentifierService.get_identifiers("CUST-001")
        assert len(identifiers) == 2
