-- 007: Lemon Squeezy entitlements — purchase → activation records.
-- Lets a cancelled/refunded subscription stop activating a license key.
-- Table-guarded (the Sequelize-owned base schema may not exist in the CI
-- scratch DB) and idempotent.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = current_schema() AND table_name = 'license_entitlements'
  ) THEN
    CREATE TABLE license_entitlements (
      id serial PRIMARY KEY,
      license_key varchar(255) NOT NULL UNIQUE,
      variant_name varchar(120),
      order_id varchar(64),
      store_id varchar(64),
      customer_email varchar(255),
      customer_name varchar(255),
      status varchar(20) NOT NULL DEFAULT 'active',
      license_valid boolean NOT NULL DEFAULT false,
      license_status varchar(30),
      activated_at timestamp,
      expires_at timestamp,
      created_at timestamp NOT NULL DEFAULT NOW()
    );
    CREATE INDEX idx_license_entitlements_status ON license_entitlements (status);
    CREATE INDEX idx_license_entitlements_order ON license_entitlements (order_id);
  END IF;
END $$;