# Source of Truth: Customer Identity Ownership

> Cross-cutting concern for the entire Shopman Suite.

---

## The Rule

**Guestman is the single source of truth for customer identity across the Shopman Suite.**

Every other app either reads customer data from Guestman (via service calls or adapter protocols) or stores a frozen snapshot at a point in time. No other app creates, modifies, or owns customer records.

This rule applies to all customer-related data: name, contact points (phone, email, WhatsApp, Instagram), documents (CPF/CNPJ), addresses, group membership, and external identities.

---

## How Each App Relates to Customer Identity

### Guestman (CRM) -- the owner

Guestman owns the canonical `Customer` record and all associated data:

- **Customer**: `code`, `uuid`, `first_name`, `last_name`, `customer_type`, `document`, `email`, `phone`, `group`, `is_active`, `metadata`.
- **ContactPoint**: all contact channels with verification status. Source of truth for whether a phone or email is verified and by which method.
- **ExternalIdentity**: links to external providers (Manychat, WhatsApp Business, Instagram, Google, Apple).
- **CustomerIdentifier** (contrib): cross-channel deduplication table for resolving a customer from any identifier.
- **CustomerAddress**: structured addresses with Google Places integration.

All mutations to customer identity go through `guestman.services.customer` (create, update) or the relevant contrib services. These emit signals (`customer_created`, `customer_updated`) that other apps can listen to.

### Omniman (Order Management) -- snapshot consumer

Omniman stores a **denormalized snapshot** of customer information inside `Order.data` at the moment the order is committed. This snapshot includes customer name, code, contact info, and delivery address as they existed at order time.

**Why a snapshot?** Orders are immutable business records. If a customer changes their name or address after placing an order, the order must still reflect the original data for invoicing, compliance, and dispute resolution.

**Data flow:**
```
Guestman.Customer (live) --> Omniman reads at commit time --> Order.data (frozen snapshot)
```

Omniman never writes back to Guestman. The relationship is strictly one-directional at write time.

For analytics, Guestman reads order history *from* Omniman through the `OrderHistoryBackend` protocol (`guestman.protocols.orders`). This is configured via:
```python
GUESTMAN = {
    "ORDER_HISTORY_BACKEND": "guestman.adapters.omniman_orders.OmnimanOrderHistoryBackend",
}
```

This reverse read is used exclusively by `InsightService.recalculate()` to compute RFM scores, LTV, churn risk, and frequency metrics.

### Doorman (Authentication) -- identity resolver

Doorman handles authentication (OTP, magic links, OAuth, sessions, tokens). It does not store customer records. Instead, it resolves customer identity by calling Guestman through the `CustomerResolver` protocol.

**Adapter:** `guestman.adapters.doorman.GuestmanCustomerResolver`

**Protocol methods:**
- `get_by_phone(phone)` -- lookup during OTP login
- `get_by_email(email)` -- lookup during email login
- `get_by_uuid(uuid)` -- lookup from session/token
- `create_for_phone(phone)` -- auto-create customer on first login (code: `WEB-<uuid8>`)

**Data flow:**
```
User authenticates --> Doorman calls CustomerResolver --> Guestman returns DoormanCustomerInfo
                                                     --> Doorman creates session referencing customer UUID
```

Doorman never stores customer data beyond the UUID reference in the session/token. If Doorman needs to display a customer name, it resolves it from Guestman at request time.

### Offerman (Pricing) -- reference consumer

Offerman may reference customers to resolve which price list applies. It calls `guestman.services.customer.price_list(code)` which returns the `price_list_code` from the customer's group.

Offerman never stores customer data. It uses the customer code as a lookup key and receives only the price list code in return.

**Data flow:**
```
Offerman needs pricing --> calls price_list("CUST-001") --> Guestman returns "PL-WHOLESALE" or None
```

### Stockman (Inventory) -- no relationship

Stockman manages inventory, stock levels, warehouses, and stock movements. It has no knowledge of customers and never references customer data. Stock operations are identified by product/SKU, not by customer.

### Craftsman (Production) -- no relationship

Craftsman manages recipes, production orders, and manufacturing workflows. It operates entirely in the product/recipe domain and never references customer data.

---

## Consequences of This Pattern

1. **Single update point.** To change a customer's phone number, you update it in Guestman. All apps that need the current phone will read it from Guestman. Historical records (like past orders in Omniman) retain the old phone in their snapshots.

2. **No distributed identity.** There is no cross-app sync process for customer data. Other apps either read live from Guestman or accept that their snapshot is frozen.

3. **Deduplication lives in Guestman.** Cross-channel customer resolution (same person on WhatsApp, Instagram, and email) is handled by `IdentifierService` and `ContactPoint`. Other apps do not attempt their own deduplication.

4. **Verification status is authoritative.** When Guestman says a phone is verified via `channel_asserted`, that is the truth for the entire suite. Doorman marks verification through Guestman's `ContactPoint.mark_verified()`.

5. **Customer deletion/deactivation propagates by reference.** Setting `is_active=False` on a Customer in Guestman means all service functions across the suite will stop returning that customer (all lookups filter `is_active=True`). Historical records in Omniman are unaffected.
