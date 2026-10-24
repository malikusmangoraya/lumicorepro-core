-- 008: order source tagging + restaurant reservation columns
--
-- Why:
--   * The `orders` table is shared by every vertical. Without a `source` column a
--     restaurant listing or admin mutation cannot exclude store orders, so
--     routes/restaurant.routes.js had to read across product lines.
--   * Restaurant reservations write the shared `bookings` table, which had no
--     tenant column, no slot instant, and no place for the diner payload. The
--     healthcare-only NOT NULLs (`doctor_id`, `reason`, `patientInfo`) also made a
--     table booking impossible to insert.
--
-- Notes / caveats:
--   * Run with the migration runner (database/migrations/migrate.js). The runner
--     splits on the statement terminator and wraps the version in one
--     transaction, so no statement here may contain a semicolon of its own.
--   * `bookings` is created by sequelize.sync() in development; on a managed
--     database the bookings vertical must already exist before this runs.
--   * Relaxing a NOT NULL loses no data, so backfill of the new tenant column
--     happens before the constraints are added.

-- ── 1. Order source ───────────────────────────────────────────────────────
ALTER TABLE orders ADD COLUMN IF NOT EXISTS source VARCHAR(30) NOT NULL DEFAULT 'ecommerce';
CREATE INDEX IF NOT EXISTS idx_orders_org_source_status ON orders (org_id, source, status);

-- A self-collection (restaurant pickup) order legitimately has no delivery address.
ALTER TABLE orders ALTER COLUMN "shippingAddress" DROP NOT NULL;

-- ── 2. Booking tenant + slot ──────────────────────────────────────────────
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS org_id INTEGER;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS "startAt" TIMESTAMP WITH TIME ZONE;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS metadata JSONB;

UPDATE bookings b SET org_id = u.current_org_id FROM users u WHERE b.org_id IS NULL AND b.user_id = u.id AND u.current_org_id IS NOT NULL;

ALTER TABLE bookings DROP CONSTRAINT IF EXISTS fk_bookings_org;
ALTER TABLE bookings ADD CONSTRAINT fk_bookings_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL ON UPDATE CASCADE;

CREATE INDEX IF NOT EXISTS idx_bookings_org ON bookings (org_id);
CREATE INDEX IF NOT EXISTS idx_bookings_org_start ON bookings (org_id, "startAt");
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings (user_id);

-- Healthcare-only columns: a table booking has no doctor, no clinical reason and
-- no patient, so the database must not demand them.
ALTER TABLE bookings ALTER COLUMN doctor_id DROP NOT NULL;
ALTER TABLE bookings ALTER COLUMN reason DROP NOT NULL;
ALTER TABLE bookings ALTER COLUMN "patientInfo" DROP NOT NULL;
