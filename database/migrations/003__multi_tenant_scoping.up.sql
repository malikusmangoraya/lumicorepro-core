-- 003: enforce multi-tenant (org_id) scoping, soft deletes, constraints + indexes
--
-- BACKFILL ASSUMPTION (documented, applied below in this order):
--   1. A row belongs to the organization its owning user is currently active in
--      (users.current_org_id) — products via vendor_id, orders/carts via user_id,
--      payments via order_id then user_id, reviews via their product.
--   2. Any row still unscoped falls back to the OLDEST organization in the
--      database (lowest id) — i.e. the pre-multi-tenant data is assigned to the
--      first tenant created during the migration to organizations.
--   3. If the database has no organization at all (pure single-tenant install),
--      org_id stays NULL. NULL means "legacy single-tenant row" and is only
--      visible to callers with no organization context.
--   Soft-deleted organizations are excluded from step 2 so rows are never
--   attached to an organization that is already gone.
--
-- Notes / caveats:
--   * Run with the migration runner (database/migrations/migrate.js). The runner
--     splits the file on the statement terminator and wraps the whole version in
--     one transaction, so no statement here may contain a semicolon of its own.
--   * `uq_products_org_sku` fails if two products of the SAME organization share
--     a non-null sku. Deduplicate those rows before running the migration.
--   * `uq_orders_order_number` fails if duplicate order numbers already exist.
--   * Before this version, models/Organization.js used Sequelize's default
--     paranoid column ("deletedAt") while the model also declared `deleted_at`.
--     Step 7 converges them onto `deleted_at` (see the comment there).

-- ── 1. Tenant + soft-delete columns ────────────────────────────────────────
ALTER TABLE products ADD COLUMN IF NOT EXISTS org_id BIGINT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS org_id BIGINT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS org_id BIGINT;
ALTER TABLE carts ADD COLUMN IF NOT EXISTS org_id BIGINT;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS org_id BIGINT;

-- ── 2. Backfill from the owning user's active organization ─────────────────
UPDATE products p SET org_id = u.current_org_id FROM users u WHERE p.org_id IS NULL AND p.vendor_id = u.id AND u.current_org_id IS NOT NULL;
UPDATE orders o SET org_id = u.current_org_id FROM users u WHERE o.org_id IS NULL AND o.user_id = u.id AND u.current_org_id IS NOT NULL;
UPDATE carts c SET org_id = u.current_org_id FROM users u WHERE c.org_id IS NULL AND c.user_id = u.id AND u.current_org_id IS NOT NULL;
UPDATE payments p SET org_id = u.current_org_id FROM users u WHERE p.org_id IS NULL AND p.user_id = u.id AND u.current_org_id IS NOT NULL;
UPDATE payments p SET org_id = o.org_id FROM orders o WHERE p.org_id IS NULL AND p.order_id = o.id AND o.org_id IS NOT NULL;
UPDATE reviews r SET org_id = p.org_id FROM products p WHERE r.org_id IS NULL AND r.product_id = p.id AND p.org_id IS NOT NULL;

-- ── 3. Fallback: orphan rows belong to the oldest (first) organization ─────
UPDATE products SET org_id = (SELECT id FROM organizations WHERE deleted_at IS NULL ORDER BY id ASC LIMIT 1) WHERE org_id IS NULL AND EXISTS (SELECT 1 FROM organizations WHERE deleted_at IS NULL);
UPDATE orders SET org_id = (SELECT id FROM organizations WHERE deleted_at IS NULL ORDER BY id ASC LIMIT 1) WHERE org_id IS NULL AND EXISTS (SELECT 1 FROM organizations WHERE deleted_at IS NULL);
UPDATE carts SET org_id = (SELECT id FROM organizations WHERE deleted_at IS NULL ORDER BY id ASC LIMIT 1) WHERE org_id IS NULL AND EXISTS (SELECT 1 FROM organizations WHERE deleted_at IS NULL);
UPDATE payments SET org_id = (SELECT id FROM organizations WHERE deleted_at IS NULL ORDER BY id ASC LIMIT 1) WHERE org_id IS NULL AND EXISTS (SELECT 1 FROM organizations WHERE deleted_at IS NULL);
UPDATE reviews SET org_id = (SELECT id FROM organizations WHERE deleted_at IS NULL ORDER BY id ASC LIMIT 1) WHERE org_id IS NULL AND EXISTS (SELECT 1 FROM organizations WHERE deleted_at IS NULL);

-- ── 4. Foreign keys (drop-then-add keeps this re-runnable) ─────────────────
ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_org;
ALTER TABLE products ADD CONSTRAINT fk_products_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS fk_orders_org;
ALTER TABLE orders ADD CONSTRAINT fk_orders_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE reviews DROP CONSTRAINT IF EXISTS fk_reviews_org;
ALTER TABLE reviews ADD CONSTRAINT fk_reviews_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE carts DROP CONSTRAINT IF EXISTS fk_carts_org;
ALTER TABLE carts ADD CONSTRAINT fk_carts_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE payments DROP CONSTRAINT IF EXISTS fk_payments_org;
ALTER TABLE payments ADD CONSTRAINT fk_payments_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;

-- ── 5. Unique constraints implied by the schema ────────────────────────────
-- Order numbers stay globally unique. A duplicate constraint created by
-- sequelize.sync() on older installs (either spelling of its generated name) is
-- replaced by one named unique index.
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_orderNumber_key;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_ordernumber_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_order_number ON orders ("orderNumber");
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_org_sku ON products (org_id, sku);

-- ── 6. Indexes on every column the routes filter by ────────────────────────
CREATE INDEX IF NOT EXISTS idx_products_org ON products (org_id);
CREATE INDEX IF NOT EXISTS idx_products_org_active ON products (org_id, isActive);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_vendor ON products (vendor_id);
CREATE INDEX IF NOT EXISTS idx_products_created_at ON products ("createdAt");
CREATE INDEX IF NOT EXISTS idx_products_deleted_at ON products (deleted_at);
CREATE INDEX IF NOT EXISTS idx_orders_org ON orders (org_id);
CREATE INDEX IF NOT EXISTS idx_orders_org_status ON orders (org_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders (user_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders ("createdAt");
CREATE INDEX IF NOT EXISTS idx_orders_deleted_at ON orders (deleted_at);
CREATE INDEX IF NOT EXISTS idx_reviews_org ON reviews (org_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews (product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews (user_id);
CREATE INDEX IF NOT EXISTS idx_carts_org ON carts (org_id);
CREATE INDEX IF NOT EXISTS idx_carts_user ON carts (user_id);
CREATE INDEX IF NOT EXISTS idx_payments_org ON payments (org_id);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments (user_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments (order_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments (status);
CREATE INDEX IF NOT EXISTS idx_organizations_deleted_at ON organizations (deleted_at);

-- ── 7. Organization soft deletes: converge "deletedAt" onto deleted_at ─────
-- models/Organization.js declares `deleted_at` but paranoid defaulted to
-- `deletedAt`, so pre-003 soft deletes were written to `"deletedAt"`. Copy them
-- across (guarded by ADD COLUMN IF NOT EXISTS so this also works on fresh
-- databases that never had the legacy column), then drop the legacy column.
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS "deletedAt" TIMESTAMP WITH TIME ZONE;
UPDATE organizations SET deleted_at = "deletedAt" WHERE deleted_at IS NULL AND "deletedAt" IS NOT NULL;
ALTER TABLE organizations DROP COLUMN IF EXISTS "deletedAt";
