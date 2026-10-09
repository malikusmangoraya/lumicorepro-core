-- Rollback of 005__audit_log_hash_chain.sql (table-guarded for the CI scratch DB)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = current_schema() AND table_name = 'audit_logs'
  ) THEN
    ALTER TABLE audit_logs DROP COLUMN IF EXISTS hash;
    ALTER TABLE audit_logs DROP COLUMN IF EXISTS prev_hash;
    DROP INDEX IF EXISTS idx_audit_logs_created_at_id;
  END IF;
END $$;
