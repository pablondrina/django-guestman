# Guestman Contracts

> django-guestman v0.2.0 -- Customer management (CRM) for the Shopman Suite.

---

## Public API

### Customer Service (`guestman.services.customer`)

| Function | Signature | Returns | Notes |
|---|---|---|---|
| `get` | `(code: str)` | `Customer \| None` | By unique code; filters `is_active=True`, `select_related("group")` |
| `get_by_uuid` | `(uuid: str)` | `Customer \| None` | By UUID field |
| `get_by_document` | `(document: str)` | `Customer \| None` | Strips non-digits before lookup |
| `get_by_phone` | `(phone: str)` | `Customer \| None` | Normalizes to E.164 first; handles `MultipleObjectsReturned` |
| `get_by_email` | `(email: str)` | `Customer \| None` | Case-insensitive match |
| `validate` | `(code: str)` | `CustomerValidation` | Full validation result with name, group, price list, default address |
| `price_list` | `(code: str)` | `str \| None` | Returns `price_list_code` from customer group (for Offerman) |
| `search` | `(query: str, limit=20)` | `list[Customer]` | Searches code, name, document, phone, email |
| `groups` | `()` | `list[CustomerGroup]` | All customer groups |
| `create` | `(code, first_name, ...)` | `Customer` | Atomic; emits `customer_created` signal |
| `update` | `(code, **fields)` | `Customer \| None` | Whitelist: `first_name, last_name, customer_type, document, email, phone, group, notes, metadata, is_active, source_system`; emits `customer_updated` with changes dict |

### Address Service (`guestman.services.address`)

| Function | Signature | Returns | Notes |
|---|---|---|---|
| `addresses` | `(customer_code)` | `list[CustomerAddress]` | All addresses for customer |
| `default_address` | `(customer_code)` | `CustomerAddress \| None` | The `is_default=True` address |
| `add_address` | `(customer_code, label, formatted_address, ...)` | `CustomerAddress` | Atomic; accepts Google Places components + coordinates |
| `set_default_address` | `(customer_code, address_id)` | `CustomerAddress` | Atomic; demotes previous default |
| `delete_address` | `(customer_code, address_id)` | `bool` | Hard delete |

### Contrib Services

| Service | Module | Key Methods |
|---|---|---|
| `ConsentService` | `guestman.contrib.consent` | `grant_consent`, `revoke_consent`, `has_consent`, `get_consents`, `get_opted_in_channels`, `get_marketable_customers` |
| `LoyaltyService` | `guestman.contrib.loyalty` | `enroll`, `get_account`, `get_balance`, `earn_points`, `redeem_points`, `add_stamp`, `get_transactions` |
| `TimelineService` | `guestman.contrib.timeline` | `log_event`, `get_timeline`, `get_recent_across_customers` |
| `IdentifierService` | `guestman.contrib.identifiers` | `find_by_identifier`, `add_identifier`, `find_or_create_customer`, `get_identifiers` |
| `InsightService` | `guestman.contrib.insights` | `get_insight`, `recalculate`, `recalculate_all`, `get_segment_customers`, `get_at_risk_customers` |
| `ManychatService` | `guestman.contrib.manychat` | `sync_subscriber` |
| `PreferenceService` | `guestman.contrib.preferences` | `get_preference`, `set_preference`, `get_preferences`, `get_preferences_dict`, `delete_preference`, `get_restrictions` |

### Signals (`guestman.signals`)

| Signal | Sender | Extra kwargs | Emitted by |
|---|---|---|---|
| `customer_created` | `Customer` | `customer` | `services.customer.create()` |
| `customer_updated` | `Customer` | `customer`, `changes` | `services.customer.update()` |

### Exceptions (`guestman.exceptions`)

`GuestmanError(BaseError)` with structured error codes: `CUSTOMER_NOT_FOUND`, `ADDRESS_NOT_FOUND`, `DUPLICATE_CONTACT`, `INVALID_PHONE`, `MERGE_DENIED`, `CONSENT_NOT_FOUND`, `LOYALTY_NOT_ENROLLED`, `LOYALTY_INSUFFICIENT_POINTS`.

---

## Invariants

1. **Customer is the source of truth for identity in the suite.** No other app owns customer data. Omniman stores a snapshot; Doorman resolves identity via Guestman adapter.

2. **Phone/email sync to ContactPoint on save.** `Customer.save()` calls `_sync_contact_points()` which creates or updates the primary ContactPoint for phone and email types. Customer.phone and Customer.email are quick-access cache fields; ContactPoint is the source of truth for verification status.

3. **One primary ContactPoint per type per customer.** Enforced by DB constraint `guestman_unique_primary_per_type` (unique on `customer, type` where `is_primary=True`). When a new primary is set, existing primaries for that type are demoted atomically.

4. **ContactPoint (type, value_normalized) is globally unique.** Enforced by DB constraint `guestman_unique_contact_value`. A phone number or email can belong to exactly one customer. Gate G1 validates this before writes.

5. **Consent is per-channel, auditable.** One record per (customer, channel). Default status is `pending` (no communication allowed). `consented_at` and `revoked_at` timestamps are preserved for LGPD/GDPR audit trail. Only `opted_in` status permits marketing communication.

6. **Loyalty transactions are append-only (ledger).** `LoyaltyTransaction` records are never modified or deleted. Every earn, redeem, adjustment, stamp, and expiration is an immutable log entry with `balance_after` for reconciliation. Account mutations use `select_for_update()` to prevent lost updates under concurrency.

7. **Manychat webhooks: HMAC + replay protection.** Inbound webhooks pass through G4 (HMAC-SHA256 signature validation with timestamp freshness) and G5 (nonce-based replay protection persisted in ProcessedEvent table).

8. **ExternalIdentity (provider, provider_uid) is globally unique.** Enforced by DB constraint `guestman_unique_external_identity`.

9. **CustomerIdentifier (identifier_type, identifier_value) is globally unique.** Enforced by DB constraint `guestman_unique_identifier`. Used for cross-channel deduplication.

---

## Gates

| Gate | Name | Validates |
|---|---|---|
| **G1** | ContactPointUniqueness | `(type, value_normalized)` does not exist in another customer. Raises `GateError` with existing customer details if violated. |
| **G2** | PrimaryInvariant | At most 1 `is_primary=True` per `(customer, type)`. Detects data corruption (should never fire in normal operation due to DB constraints). |
| **G3** | VerifiedTransition | Verification method must be in the allowed set: `channel_asserted`, `otp_whatsapp`, `otp_sms`, `email_link`, `manual`. Prevents setting arbitrary verification methods. |
| **G4** | ProviderEventAuthenticity | Webhook body matches HMAC-SHA256 signature. Validates `sha256=<hex>` format. Checks timestamp freshness (default max age: 300s). Skips validation when secret is empty (dev mode, logged as warning). |
| **G5** | ReplayProtection | Event nonce has not been processed before. Uses `ProcessedEvent` table with unique constraint for distributed-safe deduplication. Old events cleaned up via `ProcessedEvent.cleanup_old_events(days)`. |
| **G6** | MergeSafety | Customer merge requires at least one piece of strong evidence: `staff_override`, `same_verified_phone`, `same_verified_email`, or `same_verified_whatsapp`. Prevents accidental merges. Source and target must differ. |

Every gate has two call styles:
- `Gates.<gate>(...)` -- raises `GateError` on failure, returns `GateResult` on success.
- `Gates.check_<gate>(...)` -- returns `bool`, never raises.

---

## Idempotency

| Operation | Safe to retry? | Mechanism |
|---|---|---|
| `customer_service.get`, `get_by_*`, `validate`, `price_list`, `search` | Yes | Read-only |
| `customer_service.create` | No | `code` is unique; second call raises `IntegrityError` |
| `customer_service.update` | Yes | Sets fields to same values; signal only fires if changes detected |
| `address.add_address` | No | Creates a new record each time |
| `address.set_default_address` | Yes | Atomic demote+promote; same result on repeat |
| `ConsentService.grant_consent` | Yes | `update_or_create` on (customer, channel) |
| `ConsentService.revoke_consent` | Yes | `update_or_create` on (customer, channel) |
| `ConsentService.has_consent` | Yes | Read-only |
| `LoyaltyService.enroll` | Yes | `get_or_create` on customer |
| `LoyaltyService.earn_points` | No | Appends transaction; balance changes each call |
| `LoyaltyService.redeem_points` | No | Appends transaction; may fail on insufficient balance |
| `LoyaltyService.add_stamp` | No | Appends transaction; stamp count changes each call |
| `TimelineService.log_event` | No | Creates a new event record each time |
| `IdentifierService.add_identifier` | No | Unique constraint on (type, value); second call raises `IntegrityError` |
| `IdentifierService.find_or_create_customer` | Yes | Finds existing first; creates atomically only if absent |
| `ManychatService.sync_subscriber` | Yes | Finds by Manychat ID or other identifiers; updates are additive (only fills empty fields) |
| `PreferenceService.set_preference` | Yes | `update_or_create` on (customer, category, key) |
| `InsightService.recalculate` | Yes | Overwrites calculated fields; same input produces same output |
| `Gates.replay_protection` | No | First call records nonce; second call raises `GateError` (by design) |

---

## Integration Points

### Doorman Adapter (`guestman.adapters.doorman`)

`GuestmanCustomerResolver` implements Doorman's `CustomerResolver` protocol (`doorman.protocols.customer`):

| Protocol Method | Implementation |
|---|---|
| `get_by_phone(phone)` | Delegates to `customer_service.get_by_phone`, maps to `DoormanCustomerInfo` |
| `get_by_email(email)` | Delegates to `customer_service.get_by_email`, maps to `DoormanCustomerInfo` |
| `get_by_uuid(uuid)` | Delegates to `customer_service.get_by_uuid`, maps to `DoormanCustomerInfo` |
| `create_for_phone(phone)` | Creates customer with auto-generated code (`WEB-<uuid8>`), maps to `DoormanCustomerInfo` |

`DoormanCustomerInfo` carries: `uuid`, `name`, `phone`, `email`, `is_active`.

### Omniman (Order Management)

- **Customer snapshot**: Omniman stores a denormalized copy of customer info in `Order.data` at commit time. This snapshot is immutable once the order is created.
- **Order history**: Guestman reads order data through the `OrderHistoryBackend` protocol (`guestman.protocols.orders`). Configured via `GUESTMAN["ORDER_HISTORY_BACKEND"]` setting. The backend provides `get_customer_orders()` and `get_order_stats()` used by `InsightService.recalculate()`.

### Offerman (Pricing)

- Offerman may call `customer_service.price_list(code)` to resolve a customer's applicable price list code (derived from `CustomerGroup.price_list_code`).

---

## What is NOT Guestman's Job

| Concern | Owner | Guestman's role |
|---|---|---|
| **Authentication** (login, OTP, sessions, tokens) | **Doorman** | Provides `CustomerResolver` adapter. Does not handle auth flows. |
| **Orders** (cart, checkout, fulfillment) | **Omniman** | Provides customer identity for order creation. Receives order history via `OrderHistoryBackend` protocol for insights. |
| **Inventory** (stock, warehouses) | **Stockman** | None. Stockman never references customers. |
| **Production** (recipes, manufacturing) | **Craftsman** | None. Craftsman never references customers. |
| **Pricing** (price lists, rules, discounts) | **Offerman** | Provides `price_list_code` lookup. Does not own pricing logic. |
