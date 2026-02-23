# CRM Contrib Modules

> Optional modules that extend Guestman's core customer management with specialized CRM capabilities.

Each contrib is a separate Django app installed via `INSTALLED_APPS`. All are optional. The core (`guestman.models.Customer`, `ContactPoint`, `CustomerAddress`, `ExternalIdentity`) works without any of them.

---

## Consent (`guestman.contrib.consent`)

**Purpose:** LGPD/GDPR-compliant communication opt-in/opt-out tracking per channel.

**When to use:** When your business sends marketing communications (WhatsApp campaigns, email newsletters, SMS promotions, push notifications) and must comply with data protection regulations. Required for any Brazilian operation under LGPD.

**Core model:** `CommunicationConsent` -- one record per (customer, channel). Tracks status (`opted_in`, `opted_out`, `pending`), legal basis, source of consent, IP address, and timestamps for both consent grant and revocation.

**Key behavior:**
- Default status is `pending` -- no communication is allowed until the customer explicitly opts in.
- `has_consent()` returns `True` only for `opted_in` status. This is the primary check before sending any marketing message.
- `revoke_consent()` is immediate. The `revoked_at` timestamp is preserved alongside `consented_at` for a complete audit trail.
- `get_marketable_customers(channel)` returns all customer codes with active consent for a given channel -- useful for building campaign audiences.

**Service:** `ConsentService` with methods `grant_consent`, `revoke_consent`, `has_consent`, `get_consents`, `get_opted_in_channels`, `get_marketable_customers`.

**Channels:** `whatsapp`, `email`, `sms`, `push`.

**Legal bases:** `consent`, `legitimate_interest`, `contract`, `legal_obligation`.

---

## Loyalty (`guestman.contrib.loyalty`)

**Purpose:** Native loyalty program supporting both points-based and stamp-based programs with automatic tier management.

**When to use:** When your business runs a customer loyalty program. Supports two modes that can coexist: points (earn and redeem, like airline miles) and stamps (collect toward a reward, like coffee stamp cards).

**Core models:**
- `LoyaltyAccount` -- one per customer. Tracks `points_balance`, `lifetime_points`, `stamps_current`, `stamps_target`, `stamps_completed`, and `tier` (Bronze/Silver/Gold/Platinum).
- `LoyaltyTransaction` -- immutable ledger of every point/stamp operation. Records `transaction_type` (earn, redeem, adjust, expire, stamp), `points`, `balance_after`, `description`, and `reference`.

**Key behavior:**
- Transactions are **append-only**. They are never modified or deleted. Each transaction records `balance_after` for reconciliation.
- All balance mutations use `select_for_update()` inside `transaction.atomic()` to prevent lost-update race conditions under concurrent requests.
- `enroll()` is idempotent -- calling it on an already-enrolled customer returns the existing account.
- Tier auto-upgrades based on `lifetime_points` thresholds: Bronze (0), Silver (500), Gold (2000), Platinum (5000).
- When `stamps_current` reaches `stamps_target`, the card auto-completes: current resets to 0, `stamps_completed` increments.

**Service:** `LoyaltyService` with methods `enroll`, `get_account`, `get_balance`, `earn_points`, `redeem_points`, `add_stamp`, `get_transactions`.

---

## Timeline (`guestman.contrib.timeline`)

**Purpose:** Unified chronological log of every meaningful customer interaction.

**When to use:** When you need a CRM-style interaction history ("what happened with this customer?"). Essential for customer service agents who need context, for AI-powered personalization, and for CRM dashboards.

**Core model:** `TimelineEvent` -- records `event_type`, `title`, `description`, `channel`, `reference`, `metadata`, and audit fields.

**Event types:** `order`, `contact`, `note`, `visit`, `loyalty`, `system`.

**Key behavior:**
- Events are purely additive. Each `log_event()` call creates a new record.
- Events are ordered by `-created_at` (most recent first).
- `get_recent_across_customers()` provides a global activity feed for CRM dashboards.
- The `reference` field links events to external entities (e.g., `order:123`, `ticket:456`).
- The `metadata` JSONField allows free-form structured data per event.

**Service:** `TimelineService` with methods `log_event`, `get_timeline`, `get_recent_across_customers`.

---

## Identifiers (`guestman.contrib.identifiers`)

**Purpose:** Cross-channel customer deduplication. Maps external identifiers from multiple channels to a single customer.

**When to use:** When customers interact through multiple channels (WhatsApp, Instagram, Facebook, Telegram, email) and you need to resolve all interactions to a single customer record. Required by the Manychat contrib.

**Core model:** `CustomerIdentifier` -- maps `(identifier_type, identifier_value)` to a customer. Globally unique constraint ensures one-to-one mapping. Supports `is_primary` flag per type per customer.

**Identifier types:** `phone`, `email`, `instagram`, `facebook`, `whatsapp`, `telegram`, `manychat`.

**Key behavior:**
- `find_by_identifier()` first checks the `CustomerIdentifier` table, then optionally falls back to `Customer.email`/`Customer.phone` native fields.
- `find_or_create_customer()` is the primary entry point for channel integrations -- finds existing customer or creates a new one atomically with the identifier linked.
- Values are normalized on save: phone numbers to E.164, emails to lowercase, Instagram handles cleaned.

**Service:** `IdentifierService` with methods `find_by_identifier`, `add_identifier`, `find_or_create_customer`, `get_identifiers`.

---

## Insights (`guestman.contrib.insights`)

**Purpose:** Calculated customer analytics including LTV, RFM segmentation, churn risk, and behavioral patterns.

**When to use:** When you need data-driven customer segmentation for marketing campaigns, retention programs, or personalized experiences. Requires order history access via the `OrderHistoryBackend` protocol.

**Core model:** `CustomerInsight` -- one per customer (OneToOneField). Stores calculated metrics: `total_orders`, `total_spent_q`, `average_ticket_q`, frequency metrics, temporal patterns (preferred weekday/hour), RFM scores (1-5 each for recency, frequency, monetary), `rfm_segment`, `churn_risk`, and `predicted_ltv_q`.

**RFM segments:** `champion`, `loyal_customer`, `recent_customer`, `at_risk`, `lost`, `regular`.

**Key behavior:**
- Insights are not real-time -- they are recalculated on demand via `recalculate(customer_code)` or in batch via `recalculate_all()`.
- Calculation depends on the `OrderHistoryBackend` protocol (typically implemented by an Omniman adapter). Without a configured backend, metrics reset to zero.
- `get_at_risk_customers(min_churn_risk)` returns customers above a churn threshold -- useful for targeted retention campaigns.
- `get_segment_customers(segment)` returns customers by RFM segment -- useful for behavior-based marketing.
- All monetary values are stored in centavos (integer) to avoid floating-point issues. Properties `total_spent` and `average_ticket` return `Decimal` values divided by 100.

**Service:** `InsightService` with methods `get_insight`, `recalculate`, `recalculate_all`, `get_segment_customers`, `get_at_risk_customers`.

**Configuration:**
```python
GUESTMAN = {
    "ORDER_HISTORY_BACKEND": "guestman.adapters.omniman_orders.OmnimanOrderHistoryBackend",
}
```

---

## Preferences (`guestman.contrib.preferences`)

**Purpose:** Per-customer preference storage for explicit declarations, inferred patterns, and restrictions.

**When to use:** When you need to store customer-specific preferences such as dietary restrictions (lactose-free, gluten-free), flavor preferences, packaging choices, or any key-value preference that influences how you serve the customer.

**Core model:** `CustomerPreference` -- keyed by `(customer, category, key)` with a JSONField `value` that can hold booleans, strings, lists, or any JSON-serializable type. Includes `preference_type` (explicit, inferred, restriction), `confidence` score (0.00-1.00 for inferred preferences), and `source` for traceability.

**Preference types:**
- `explicit` -- customer declared it directly (e.g., via a form or chat).
- `inferred` -- system detected it from behavior (e.g., always orders decaf). Carries a `confidence` score.
- `restriction` -- hard constraint (e.g., allergy). `get_restrictions()` returns only these.

**Key behavior:**
- `set_preference()` is idempotent via `update_or_create` on (customer, category, key).
- `get_preferences_dict()` returns a nested dict `{category: {key: value}}` for easy template rendering or API serialization.
- `delete_preference()` performs a hard delete.

**Service:** `PreferenceService` with methods `get_preference`, `set_preference`, `get_preferences`, `get_preferences_dict`, `delete_preference`, `get_restrictions`.

---

## How the Contribs Relate to Each Other

```
Identifiers ----> [resolves customer for] ----> Manychat (sync_subscriber)
                                                    |
                                                    v
                                              [may trigger]
                                                    |
    +-------+-------+-------+-------+               |
    |       |       |       |       |               |
    v       v       v       v       v               v
Consent  Loyalty  Timeline  Preferences  Insights  [customer created/updated]
```

**Identifiers** is the foundation for channel integrations. `ManychatService.sync_subscriber()` depends on it to find or create customers from Manychat subscriber data.

**Timeline** is the integration layer -- other contribs and external systems write events to the timeline. When loyalty points are earned, a timeline event can record it. When an order is placed, Omniman can log a timeline event. Timeline itself does not depend on other contribs.

**Consent** is independent and should be checked before any communication. Other contribs (e.g., Loyalty sending a "you earned 100 points" notification) should call `ConsentService.has_consent()` before sending.

**Loyalty** and **Insights** both deal with customer value but at different levels. Loyalty is transactional (earn/redeem/stamp in real time), while Insights is analytical (batch-calculated RFM, LTV, churn). Insights may use loyalty data as an input signal, but the two do not depend on each other at the code level.

**Preferences** is standalone -- it stores structured data that other systems read. For example, an order system might check `get_restrictions()` before suggesting products, or a marketing system might use preferences to personalize messages.

### Installation patterns

**Minimal CRM:** `guestman` only (core models + customer/address services).

**Omnichannel CRM:** `guestman` + `identifiers` + `manychat` (or other channel integrations) + `consent` + `timeline`.

**Full suite:** All contribs installed. This gives you identity resolution, communication compliance, loyalty programs, interaction history, customer analytics, and preference management.
