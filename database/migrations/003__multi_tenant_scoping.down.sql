-- 003 rollback: drop the multi-tenant scoping, soft-delete columns, constraints
-- and indexes added by 003__multi_tenant_scoping.up.sql.
--
-- The `deletedAt` column that step 7 of the up migration removed is restored and
-- re-populated from `deleted_at`, so a rollback leaves organizations consistent
-- with the pre-003 Organization model (paranoid default column).

-- ── Organizations: restore the legacy paranoid column ─────────────────────
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS "deletedAt" TIMESTAMP WITH TIME ZONE;
UPDATE organizations SET "deletedAt" = deleted_at WHERE "deletedAt" IS NULL AND deleted_at IS NOT NULL;
DROP INDEX IF EXISTS idx_organizations_deleted_at;

-- ── Indexes + unique constraints ──────────────────────────────────────────
DROP INDEX IF EXISTS uq_products_org_sku;
DROP INDEX IF EXISTS uq_orders_order_number;
DROP INDEX IF EXISTS idx_products_org;
DROP INDEX IF EXISTS idx_products_org_active;
DROP INDEX IF EXISTS idx_products_category;
DROP INDEX IF EXISTS idx_products_vendor;
DROP INDEX IF EXISTS idx_products_created_at;
DROP INDEX IF EXISTS idx_products_deleted_at;
DROP INDEX IF EXISTS idx_orders_org;
DROP INDEX IF EXISTS idx_orders_org_status;
DROP INDEX IF EXISTS idx_orders_status;
DROP INDEX IF EXISTS idx_orders_user;
DROP INDEX IF EXISTS idx_orders_created_at;
DROP INDEX IF EXISTS idx_orders_deleted_at;
DROP INDEX IF EXISTS idx_reviews_org;
DROP INDEX IF EXISTS idx_reviews_product;
DROP INDEX IF EXISTS idx_reviews_user;
DROP INDEX IF EXISTS idx_carts_org;
DROP INDEX IF EXISTS idx_carts_user;
DROP INDEX IF EXISTS idx_payments_org;
DROP INDEX IF EXISTS idx_payments_user;
DROP INDEX IF EXISTS idx_payments_order;
DROP INDEX IF EXISTS idx_payments_status;

-- ── Foreign keys ──────────────────────────────────────────────────────────
ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_org;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS fk_orders_org;
ALTER TABLE reviews DROP CONSTRAINT IF EXISTS fk_reviews_org;
ALTER TABLE carts DROP CONSTRAINT IF EXISTS fk_carts_org;
ALTER TABLE payments DROP CONSTRAINT IF EXISTS fk_payments_org;

-- ── Tenant + soft-delete columns ──────────────────────────────────────────
ALTER TABLE products DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE products DROP COLUMN IF EXISTS org_id;
ALTER TABLE orders DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE orders DROP COLUMN IF EXISTS org_id;
ALTER TABLE reviews DROP COLUMN IF EXISTS org_id;
ALTER TABLE carts DROP COLUMN IF EXISTS org_id;
ALTER TABLE payments DROP COLUMN IF EXISTS org_id;
