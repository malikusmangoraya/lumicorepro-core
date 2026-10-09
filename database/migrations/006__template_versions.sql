-- 006: Versioned template updates for sold marketplace items.
-- Admins publish a version; buyers (paid orders) are notified and download
-- the latest package. Table-guarded like 005 (the Sequelize-owned base schema
-- may not exist in the CI scratch DB; products/orders here are reference
-- documentation for the ORM-managed columns).

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = current_schema() AND table_name = 'template_versions'
  ) THEN
    CREATE TABLE template_versions (
      id serial PRIMARY KEY,
      product_id integer NOT NULL,
      version varchar(32) NOT NULL,
      changelog text,
      file_name varchar(255),
      file_sha256 varchar(64),
      file_size_bytes integer,
      published_by integer,
      is_latest boolean NOT NULL DEFAULT true,
      created_at timestamp NOT NULL DEFAULT NOW(),
      CONSTRAINT uq_template_versions_product_version UNIQUE (product_id, version)
    );
    CREATE INDEX idx_template_versions_latest ON template_versions (product_id, is_latest);
  END IF;
END $$;
