-- 004 rollback: restore the legacy BIGINT tenant columns dropped by
-- 004__postgres_integer_foreign_keys.up.sql.
--
-- Existing serial IDs fit in either integer width, so the USING cast is safe.
-- Foreign keys are recreated with the same names used by 003.

-- ── 1. Drop the INTEGER foreign keys ──────────────────────────────────────
ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_org;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS fk_orders_org;
ALTER TABLE reviews DROP CONSTRAINT IF EXISTS fk_reviews_org;
ALTER TABLE carts DROP CONSTRAINT IF EXISTS fk_carts_org;
ALTER TABLE payments DROP CONSTRAINT IF EXISTS fk_payments_org;

-- ── 2. Restore the legacy column types ───────────────────────────────────
-- The five 003 tenant columns return to BIGINT. The four columns first created
-- by 004 are dropped, returning the schema to its pre-004 shape.
ALTER TABLE products ALTER COLUMN org_id TYPE BIGINT USING org_id::BIGINT;
ALTER TABLE orders ALTER COLUMN org_id TYPE BIGINT USING org_id::BIGINT;
ALTER TABLE reviews ALTER COLUMN org_id TYPE BIGINT USING org_id::BIGINT;
ALTER TABLE carts ALTER COLUMN org_id TYPE BIGINT USING org_id::BIGINT;
ALTER TABLE payments ALTER COLUMN org_id TYPE BIGINT USING org_id::BIGINT;
ALTER TABLE users DROP COLUMN IF EXISTS current_org_id;
ALTER TABLE organizations DROP COLUMN IF EXISTS owner_id;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS user_id;
ALTER TABLE doctors DROP COLUMN IF EXISTS org_id;

-- ── 3. Restore the 003 foreign keys ───────────────────────────────────────
ALTER TABLE products ADD CONSTRAINT fk_products_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE orders ADD CONSTRAINT fk_orders_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE reviews ADD CONSTRAINT fk_reviews_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE carts ADD CONSTRAINT fk_carts_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE payments ADD CONSTRAINT fk_payments_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;
