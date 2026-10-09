-- Database Schema — Structural Contract (TRD #4)
-- Generated baseline: 14 relational entities with explicit FK contracts.
-- PostgreSQL 14+ / MySQL 8+ compatible (JSONB on Postgres, JSON on MySQL).

CREATE TABLE IF NOT EXISTS categories (
  id          BIGSERIAL PRIMARY KEY,
  name        VARCHAR(150) NOT NULL,
  slug        VARCHAR(180) UNIQUE NOT NULL,
  parent_id   BIGINT NULL REFERENCES categories(id) ON DELETE SET NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  id                 BIGSERIAL PRIMARY KEY,
  email              VARCHAR(255) UNIQUE NOT NULL,
  password_hash      VARCHAR(255) NOT NULL,        -- bcrypt (12+ rounds)
  role               VARCHAR(50) NOT NULL DEFAULT 'user'
                     CHECK (role IN ('user', 'admin', 'vendor')),
  two_factor_secret  VARCHAR(255) NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
  id           BIGSERIAL PRIMARY KEY,
  title        VARCHAR(255) NOT NULL,
  description  TEXT NOT NULL,
  price_cents  BIGINT NOT NULL CHECK (price_cents >= 0),
  stock_count  INTEGER NOT NULL DEFAULT 0 CHECK (stock_count >= 0),
  category_id  BIGINT NULL REFERENCES categories(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_products_category   ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_title_db   ON products(lower(title));

CREATE TABLE IF NOT EXISTS coupons (
  id         BIGSERIAL PRIMARY KEY,
  code       VARCHAR(50) UNIQUE NOT NULL,
  discount   NUMERIC(10,2) NOT NULL DEFAULT 0,
  user_id    BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  valid_until TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
  id               BIGSERIAL PRIMARY KEY,
  user_id          BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  coupon_id        BIGINT NULL REFERENCES coupons(id) ON DELETE SET NULL,
  total_amount     NUMERIC(12,2) NOT NULL DEFAULT 0,
  tracking_status  VARCHAR(50) NOT NULL DEFAULT 'pending'
                   CHECK (tracking_status IN ('pending','processing','shipped','delivered','cancelled','refunded')),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_orders_user    ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_coupon  ON orders(coupon_id);

CREATE TABLE IF NOT EXISTS payments (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  order_id    BIGINT NULL REFERENCES orders(id) ON DELETE SET NULL,
  amount      NUMERIC(12,2) NOT NULL,
  status      VARCHAR(50) NOT NULL DEFAULT 'pending',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_user  ON payments(user_id);

CREATE TABLE IF NOT EXISTS carts (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_carts_user ON carts(user_id);

CREATE TABLE IF NOT EXISTS cart_items (
  id          BIGSERIAL PRIMARY KEY,
  cart_id     BIGINT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
  product_id  BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  quantity    INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0)
);
CREATE INDEX IF NOT EXISTS idx_cart_items_cart    ON cart_items(cart_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_product ON cart_items(product_id);

CREATE TABLE IF NOT EXISTS reviews (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  product_id  BIGINT NULL REFERENCES products(id) ON DELETE SET NULL,
  rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment     TEXT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);

CREATE TABLE IF NOT EXISTS wishlists (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  product_id  BIGINT NULL REFERENCES products(id) ON DELETE SET NULL,
  UNIQUE (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS addresses (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  label       VARCHAR(100) NULL,
  line1       VARCHAR(255) NOT NULL,
  city        VARCHAR(120) NOT NULL,
  country     VARCHAR(120) NOT NULL,
  postcode    VARCHAR(20) NULL
);
CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id);

CREATE TABLE IF NOT EXISTS subscriptions (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  plan          VARCHAR(50) NOT NULL,
  status        VARCHAR(50) NOT NULL DEFAULT 'active',
  renews_at     TIMESTAMPTZ NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);

CREATE TABLE IF NOT EXISTS notifications (
  id           BIGSERIAL PRIMARY KEY,
  recipient_id BIGINT NULL REFERENCES users(id) ON DELETE CASCADE,
  type         VARCHAR(50) NOT NULL,
  title        VARCHAR(255) NOT NULL,
  message      TEXT NULL,
  read_at      TIMESTAMPTZ NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_id);

CREATE TABLE IF NOT EXISTS analytics_events (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  event       VARCHAR(100) NOT NULL,
  payload     JSONB NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_analytics_events_user ON analytics_events(user_id);

-- ═══ Row Lock & Concurrency Mandate (TRD #4 §2) ═══
-- Checkout MUST run inside a single DB transaction that locks each product row:
--
--   BEGIN;
--   SELECT * FROM products WHERE id = $1 AND stock_count >= $qty FOR UPDATE;
--   -- no row → insufficient stock → ROLLBACK
--   UPDATE products SET stock_count = stock_count - $qty WHERE id = $1;
--   INSERT INTO orders (user_id, coupon_id, total_amount, tracking_status) VALUES (...);
--   COMMIT;
--
-- `FOR UPDATE` serializes concurrent checkouts on the same SKU, eliminating
-- oversell without optimistic retry loops.
