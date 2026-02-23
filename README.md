# Django Guestman

Customer management for Django with flexible extensions.

## Installation

```bash
pip install django-guestman
```

```python
INSTALLED_APPS = [
    ...
    'guestman',
    'guestman.contrib.admin_unfold',  # optional, for Unfold admin
]
```

```bash
python manage.py migrate
```

## Core Concepts

### Customer
Core customer entity with basic contact info.

```python
from guestman.models import Customer

customer = Customer.objects.create(
    code="CLI-001",
    first_name="Joao",
    last_name="Silva",
    email="joao@email.com",
    phone="11999999999",
)
```

### CustomerAddress
Multiple addresses per customer.

```python
from guestman.models import CustomerAddress

address = CustomerAddress.objects.create(
    customer=customer,
    street="Rua das Flores",
    number="123",
    complement="Apto 45",
    neighborhood="Centro",
    city="Sao Paulo",
    state="SP",
    zipcode="01234-567",
    is_default=True,
)
```

## Services

### Customer Lookup

```python
from guestman.services import find_customer

# Find by code
customer = find_customer(code="CLI-001")

# Find by phone
customer = find_customer(phone="11999999999")

# Find by email
customer = find_customer(email="joao@email.com")
```

### Address Management

```python
from guestman.services import add_address, get_addresses

# Add address
address = add_address(
    customer_code="CLI-001",
    street="Rua Nova",
    number="456",
    city="Sao Paulo",
    state="SP",
    zipcode="04567-890",
)

# Get all addresses
addresses = get_addresses(customer_code="CLI-001")
```

## Multi-Channel Contacts

### ContactPoint

Manage multiple contact points per customer with verification status.

```python
from guestman.models import Customer, ContactPoint

customer = Customer.objects.get(code="CLI-001")

# Add WhatsApp contact
contact = ContactPoint.objects.create(
    customer=customer,
    type=ContactPoint.Type.WHATSAPP,
    value_normalized="+5541999998888",
    is_verified=True,
    verification_method=ContactPoint.VerificationMethod.CHANNEL_ASSERTED,
)

# Find customer by contact
contact = ContactPoint.objects.get(
    type=ContactPoint.Type.WHATSAPP,
    value_normalized="+5541999998888",
)
customer = contact.customer
```

### ExternalIdentity

Link customers to external providers (Manychat, WhatsApp Business, etc.).

```python
from guestman.models import ExternalIdentity

# Link to Manychat subscriber
identity = ExternalIdentity.objects.create(
    customer=customer,
    provider=ExternalIdentity.Provider.MANYCHAT,
    provider_uid="subscriber_123456",
    provider_meta={"tags": ["vip"], "channel": "whatsapp"},
)

# Find customer by Manychat ID
identity = ExternalIdentity.objects.get(
    provider=ExternalIdentity.Provider.MANYCHAT,
    provider_uid="subscriber_123456",
)
customer = identity.customer
```

## Contrib Modules

### guestman.contrib.identifiers
Additional identification (CPF, CNPJ, etc.).

```python
INSTALLED_APPS = [
    'guestman',
    'guestman.contrib.identifiers',
]
```

```python
from guestman.contrib.identifiers.models import CustomerIdentifier

CustomerIdentifier.objects.create(
    customer=customer,
    identifier_type="cpf",
    value="123.456.789-00",
)
```

### guestman.contrib.preferences
Customer preferences and settings.

```python
INSTALLED_APPS = [
    'guestman',
    'guestman.contrib.preferences',
]
```

```python
from guestman.contrib.preferences.models import CustomerPreference

CustomerPreference.objects.create(
    customer=customer,
    key="newsletter",
    value="true",
)
```

### guestman.contrib.insights
Customer analytics and metrics.

```python
INSTALLED_APPS = [
    'guestman',
    'guestman.contrib.insights',
]
```

```python
from guestman.contrib.insights.models import CustomerInsight

CustomerInsight.objects.create(
    customer=customer,
    metric="total_orders",
    value=Decimal("15"),
)
```

## Integration with Omniman

Link orders to customers using handle:

```python
from omniman.models import Session

# Link session to customer
Session.objects.filter(pk=session.pk).update(
    handle_type="customer",
    handle_ref=customer.code,
)

# After commit, order will have handle_ref=customer.code
```

Query orders by customer:

```python
from omniman.models import Order

orders = Order.objects.filter(
    handle_type="customer",
    handle_ref="CLI-001",
)
```

## Admin (Unfold)

```python
INSTALLED_APPS = [
    'unfold',
    ...
    'guestman',
    'guestman.contrib.admin_unfold',
]
```

Features:
- Customer search by code, name, phone, email
- Address inlines
- Order history link (if Omniman installed)

## Shopman Suite

Guestman is part of the [Shopman suite](https://github.com/pablondrina). The admin UI uses shared utilities from [django-shopman-commons](https://github.com/pablondrina/django-shopman-commons):

- `BaseModelAdmin`, `BaseTabularInline` — textarea-aware admin classes for Unfold
- `unfold_badge` — colored badge helpers

```python
from shopman_commons.contrib.admin_unfold.base import BaseModelAdmin, BaseTabularInline
from shopman_commons.contrib.admin_unfold.badges import unfold_badge
```

## Requirements

- Python 3.11+
- Django 5.0+

## License

MIT
