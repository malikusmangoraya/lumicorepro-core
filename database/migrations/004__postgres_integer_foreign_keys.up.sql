-- 004: use Postgres-native INTEGER foreign keys instead of MySQL-style unsigned BIGINT
--
-- PostgreSQL does not support UNSIGNED. The models reference INTEGER primary
-- keys, so every foreign key pointing at users.id or organizations.id must also
-- be INTEGER. ALTER ... USING ... is safe for existing serial IDs, and ADD
-- COLUMN IF NOT EXISTS keeps this re-runnable on databases that already have
-- the tenant columns from 003.

-- ── 1. Ensure every tenant column exists ─────────────────────────────────
ALTER TABLE products ADD COLUMN IF NOT EXISTS org_id INTEGER;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS org_id INTEGER;
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS org_id INTEGER;
ALTER TABLE carts ADD COLUMN IF NOT EXISTS org_id INTEGER;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS org_id INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_org_id INTEGER;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS owner_id INTEGER;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_id INTEGER;
ALTER TABLE doctors ADD COLUMN IF NOT EXISTS org_id INTEGER;

-- ── 2. Drop foreign keys before changing the constrained columns ──────────
ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_org;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS fk_orders_org;
ALTER TABLE reviews DROP CONSTRAINT IF EXISTS fk_reviews_org;
ALTER TABLE carts DROP CONSTRAINT IF EXISTS fk_carts_org;
ALTER TABLE payments DROP CONSTRAINT IF EXISTS fk_payments_org;

-- ── 3. Converge legacy BIGINT columns onto INTEGER ────────────────────────
ALTER TABLE products ALTER COLUMN org_id TYPE INTEGER USING org_id::INTEGER;
ALTER TABLE orders ALTER COLUMN org_id TYPE INTEGER USING org_id::INTEGER;
ALTER TABLE reviews ALTER COLUMN org_id TYPE INTEGER USING org_id::INTEGER;
ALTER TABLE carts ALTER COLUMN org_id TYPE INTEGER USING org_id::INTEGER;
ALTER TABLE payments ALTER COLUMN org_id TYPE INTEGER USING org_id::INTEGER;
ALTER TABLE users ALTER COLUMN current_org_id TYPE INTEGER USING current_org_id::INTEGER;
ALTER TABLE organizations ALTER COLUMN owner_id TYPE INTEGER USING owner_id::INTEGER;
ALTER TABLE audit_logs ALTER COLUMN user_id TYPE INTEGER USING user_id::INTEGER;
ALTER TABLE doctors ALTER COLUMN org_id TYPE INTEGER USING org_id::INTEGER;

-- ── 4. Restore the tenant foreign keys ────────────────────────────────────
ALTER TABLE products ADD CONSTRAINT fk_products_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE orders ADD CONSTRAINT fk_orders_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE reviews ADD CONSTRAINT fk_reviews_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE carts ADD CONSTRAINT fk_carts_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE payments ADD CONSTRAINT fk_payments_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
