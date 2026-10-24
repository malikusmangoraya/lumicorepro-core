-- 008 rollback: remove order source tagging and the reservation columns added by
-- 008__order_source_and_reservation_columns.up.sql.
--
-- WARNING: the restored NOT NULL constraints only hold while every `bookings` row
-- still has a doctor, a reason and a patient. If restaurant reservations were
-- created after 008, delete or backfill those rows first — PostgreSQL aborts the
-- statement otherwise, and the runner rolls the whole rollback back.

-- ── 1. Restore the booking constraints ────────────────────────────────────
ALTER TABLE bookings ALTER COLUMN "patientInfo" SET NOT NULL;
ALTER TABLE bookings ALTER COLUMN reason SET NOT NULL;
ALTER TABLE bookings ALTER COLUMN doctor_id SET NOT NULL;

-- ── 2. Drop the booking tenant index and columns ──────────────────────────
DROP INDEX IF EXISTS idx_bookings_org;
DROP INDEX IF EXISTS idx_bookings_org_start;
DROP INDEX IF EXISTS idx_bookings_user;
ALTER TABLE bookings DROP CONSTRAINT IF EXISTS fk_bookings_org;
ALTER TABLE bookings DROP COLUMN IF EXISTS org_id;
ALTER TABLE bookings DROP COLUMN IF EXISTS "startAt";
ALTER TABLE bookings DROP COLUMN IF EXISTS metadata;

-- ── 3. Restore the order address constraint ───────────────────────────────
UPDATE orders SET "shippingAddress" = '{}' WHERE "shippingAddress" IS NULL;
ALTER TABLE orders ALTER COLUMN "shippingAddress" SET NOT NULL;

-- ── 4. Drop the source column ─────────────────────────────────────────────
DROP INDEX IF EXISTS idx_orders_org_source_status;
ALTER TABLE orders DROP COLUMN IF EXISTS source;
