# Database Schema Configuration & Structural Contract — Apex

> TRD #4 baseline: 14 relational entities with explicit FK contracts + row-lock
> checkout concurrency. The canonical backend-library stays read-only; the
> generated `backend/` copy is verified and patched below.

## 1. Model Baseline

Models mounted: **14/14** ✓.

`User`, `Product`, `Order`, `Payment`, `Cart`, `CartItem`, `Review`, `Wishlist`, `Address`, `Coupon`, `Subscription`, `Notification`, `AnalyticsEvent`, `Category`

## 2. Foreign-Key Contracts

Verified in `backend/models/index.js`: **18** contracts, all wired.

['| `Product.category_id` | `Category.id` |', '| `Product.vendor_id` | `User.id` |', '| `Order.user_id` | `User.id` |', '| `Order.coupon_id` | `Coupon.id` |', '| `Payment.user_id` | `User.id` |', '| `Payment.order_id` | `Order.id` |', '| `Cart.user_id` | `User.id` |', '| `CartItem.cart_id` | `Cart.id` |', '| `CartItem.product_id` | `Product.id` |', '| `Review.user_id` | `User.id` |', '| `Review.product_id` | `Product.id` |', '| `Wishlist.user_id` | `User.id` |', '| `Wishlist.product_id` | `Product.id` |', '| `Address.user_id` | `User.id` |', '| `Coupon.user_id` | `User.id` |', '| `Subscription.user_id` | `User.id` |', '| `Notification.recipient_id` | `User.id` |', '| `AnalyticsEvent.user_id` | `User.id` |']

- Indices: queried columns indexed (`user_id`, `product_id`, `category_id`, `order_id`, `coupon_id`, …).
- `Order.coupon_id` → `coupons.id`: patched into the generated copy
  (**ok**), canonical library untouched.

## 3. Baseline → Canonical Field Aliases

| Model     | Baseline field      | Canonical field                                                |
| --------- | ------------------- | -------------------------------------------------------------- |
| `User`    | `id`                | `id`                                                           |
| `User`    | `email`             | `email`                                                        |
| `User`    | `password_hash`     | `password (bcrypt-hashed, excluded by default scope)`          |
| `User`    | `two_factor_secret` | `twoFactorSecret`                                              |
| `User`    | `role`              | `role ('user'                                                  | 'admin'      | 'vendor')` |
| `Product` | `id`                | `id`                                                           |
| `Product` | `title`             | `title`                                                        |
| `Product` | `description`       | `description`                                                  |
| `Product` | `price_cents`       | `price (DECIMAL(10,2), USD dollars)`                           |
| `Product` | `stock_count`       | `stock (INTEGER, guarded ≥ 0)`                                 |
| `Product` | `category_id`       | `category_id (INTEGER FK → categories.id, nullable)`           |
| `Order`   | `id`                | `id`                                                           |
| `Order`   | `user_id`           | `user_id (INTEGER FK → users.id, nullable)`                    |
| `Order`   | `coupon_id`         | `coupon_id (INTEGER FK → coupons.id, patched SCHEMA)` |
| `Order`   | `total_amount`      | `totalPrice (DECIMAL(10,2))`                                   |
| `Order`   | `tracking_status`   | `status ('pending'                                             | 'processing' | 'shipped'  | 'delivered' | 'cancelled' | 'refunded') + trackingNumber/carrier` |

## 4. Row Lock & Concurrency Mandate

Order checkout runs in a single DB transaction with isolated row locks:
**CONFORMANT**.

| Control            | Status                                               |
| ------------------ | ---------------------------------------------------- |
| `transaction`      | ✓ checkout wrapped in a single DB transaction        |
| `row_lock`         | ✓ isolated SELECT ... FOR UPDATE row lock on product |
| `stock_guard`      | ✓ stock guard checked while row is locked            |
| `atomic_decrement` | ✓ atomic stock decrement inside the same transaction |

Sources scanned: `services\orderService.js`, `routes\order.routes.js`, `routes\orderRoutes.js`.

Deployable DDL reference: `database/schemas/schema.sql`
