-- Rollback of 007__license_entitlements.sql (table-guarded)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = current_schema() AND table_name = 'license_entitlements'
  ) THEN
    DROP TABLE license_entitlements;
  END IF;
END $$;