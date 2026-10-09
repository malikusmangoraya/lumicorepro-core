-- Rollback of 006__template_versions.sql (table-guarded)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = current_schema() AND table_name = 'template_versions'
  ) THEN
    DROP TABLE template_versions;
  END IF;
END $$;
