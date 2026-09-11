# BACKEND_SCHEMA_SPEC.md — LumicorePro Database Schema Configuration & Structural Contract

> Source of truth: TRD #4 *Database Schema Configuration & Structural Contract*.
> Relational contracts, field semantics, and the concurrency mandate. Patches are
> applied to the generated copy only — the canonical library is read-only.

---

## Model Baseline

The 14-model relational baseline (Category included for `Product.category_id`):

`User`, `Product`, `Order`, `Payment`, `Cart`, `CartItem`, `Review`, `Wishlist`,
`Address`, `Coupon`, `Subscription`, `Notification`, `AnalyticsEvent`, `Category`.

All 14 must exist as Sequelize models in the generated `backend/models/`.

## Field Aliases

Canonical names stay deployed. Semantics are mapped, never renamed (renaming
breaks service code):

| Baseline | Canonical | Semantics |
|----------|-----------|-----------|
| `password` | `password_hash` | bcrypt hash, ≥ 12 rounds |
| `price` | `price_cents` | integer minor units |
| `stock` | `stock_count` | integer availability |
| `totalPrice` | `total_amount` | order money total |
| `status` | `tracking_status` | order lifecycle tracking |

## Foreign Key Contract

Verified in `backend/models/index.js` via `foreignKey: '<column>'`:

| Child | Column | Parent |
|-------|--------|--------|
| `User` | `id` (PK surrogate) | — |
| `Product` | `category_id` | `Category` |
| `Product` | `vendor_id` | `User` |
| `Order` | `user_id` | `User` |
| `Order` | `coupon_id` | `Coupon` — **structural gap, patched into generated copy** (`LUMICORE_SCHEMA`) |
| `Payment` | `user_id` | `User` |
| `Payment` | `order_id` | `Order` |
| `Cart` | `user_id` | `User` |
| `CartItem` | `cart_id` | `Cart` |
| `CartItem` | `product_id` | `Product` |
| `Review` | `user_id` | `User` |
| `Review` | `product_id` | `Product` |
| `Wishlist` | `user_id` | `User` |
| `Wishlist` | `product_id` | `Product` |
| `Address` | `user_id` | `User` |
| `Coupon` | `user_id` | `User` |
| `Subscription` | `user_id` | `User` |
| `Notification` | `recipient_id` | `User` |
| `AnalyticsEvent` | `user_id` | `User` |

## Concurrency Mandate (Row Locks)

Transactional DB queries must use isolated row-level locks:

1. **Transaction:** `sequelize.transaction()` / `sequelize.transaction(async` in the
   order flow.
2. **Row lock:** `lock: t.LOCK.UPDATE` / `FOR UPDATE` on order-critical reads.
3. **Stock guard:** reject order when purchased quantity exceeds available stock.
4. **Atomic decrement:** stock reduced atomically inside the transaction
   (no read-modify-write race).

Reference implementation: `backend/services/orderService.js` (canonical, read-only).

## Multi-Tenancy (Organizations + RBAC)

Optional extension on top of the 14-model baseline (baseline count unchanged).
When a backend opts into multi-tenancy, the following rules are enforced by the
docs-as-rule-engine gate (`project-rules/spec-lockfile.json`):

- `LUMIRULE(scope=schema, id=multitenancy, mode=required)` — every tenant-scoped
  resource carries an `org_id` foreign key (`foreignKey: 'org_id'` in
  `models/index.js`); all org-scoped routes are gated by a `requireOrg`
  middleware honoring `x-org-id` / `user.current_org_id`.
- `LUMIRULE(scope=schema, id=rbac, mode=required)` — access control via
  `Role` + `Permission` models (with a `role_permissions` join) and a
  `requirePermission` middleware; `org.members.manage` gates member changes.

Optional tables (not part of the 14-model baseline): `Organization`,
`Membership`, `Role`, `Permission`.

Reference implementation: `backend/models/`, `backend/middleware/rbac.js`,
`backend/routes/org.routes.js` (canonical, read-only).

## Conformance

| Check | Gate reference |
|-------|----------------|
| Baseline models present | `schema.checks.baseline` |
| FK contract honored (incl. `Order.coupon_id`) | `schema.checks.fk_contract` |
| Row-lock transactional order flow | `schema.checks.concurrency` |

**Hard rule:** any missing model, unresolved FK, or non-transactional order flow
is a schema violation routed to self-healing; the ZIP archive is not compiled
while this check is red.