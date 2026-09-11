-- LumicorePro — Supporting Indexes (idempotent, PostgreSQL)
-- Covers common filter/sort/pagination combos & foreign-key join paths.
-- Apply with: `psql $DATABASE_URL -f database/schemas/indexes.sql`

-- Orders: status filter + recent-first pagination
CREATE INDEX IF NOT EXISTS idx_orders_user_status_created
  ON orders (user_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_status_created
  ON orders (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_user_created
  ON orders (user_id, created_at DESC);

-- Orders: paid-revenue aggregation
CREATE INDEX IF NOT EXISTS idx_orders_paid_created
  ON orders (is_paid, created_at);

-- Products: category + active + price sort (catalog)
CREATE INDEX IF NOT EXISTS idx_products_category_active_price
  ON products (category, is_active, price);

CREATE INDEX IF NOT EXISTS idx_products_active_rating
  ON products (is_active, rating DESC);

CREATE INDEX IF NOT EXISTS idx_products_vendor
  ON products (vendor_id);

-- Products: ILIKE search is expensive; this B-tree can't speed `%term%`,
-- but an expression index on lower(title) helps prefix searches.
CREATE INDEX IF NOT EXISTS idx_products_lower_title
  ON products (lower(title));

-- Reviews: product + recency, and one-per-user uniqueness guard
CREATE INDEX IF NOT EXISTS idx_reviews_product_created
  ON reviews (product_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reviews_user_product
  ON reviews (user_id, product_id);

-- Payments: pending webhook lookups + user history
CREATE INDEX IF NOT EXISTS idx_payments_status
  ON payments (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_payments_user_created
  ON payments (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_payments_stripe_intent
  ON payments (stripe_payment_intent_id);

-- Notifications: recipient + unread desc
CREATE INDEX IF NOT EXISTS idx_notifications_recipient_created
  ON notifications (recipient_id, created_at DESC);

-- Cart items / wishlist: user-scoped lookups
CREATE INDEX IF NOT EXISTS idx_cart_items_cart
  ON cart_items (cart_id);

CREATE INDEX IF NOT EXISTS idx_cart_items_product
  ON cart_items (product_id);

CREATE INDEX IF NOT EXISTS idx_wishlists_user
  ON wishlists (user_id, created_at DESC);

-- User identity search (email normalize)
CREATE INDEX IF NOT EXISTS idx_users_lower_email
  ON users (lower(email));

-- Analytics event lookups
CREATE INDEX IF NOT EXISTS idx_analytics_user_event
  ON analytics_events (user_id, event_type);

COMMENT ON TABLE orders IS 'Composite indexes: (user_id,status,created_at) for admin order lists; (is_paid,created_at) for revenue rollups.';