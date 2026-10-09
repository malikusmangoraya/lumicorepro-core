-- 005: Tamper-evident audit trail (hash chain)
-- Each row stores sha256(prev_hash || user_id || action || ip || user_agent || meta || created_at).
-- `/api/audit-logs/verify` recomputes the chain; any edit or delete breaks it.
-- Complements the Sequelize immutability hooks (which only guard ORM paths):
-- the chain also catches raw-SQL tampering, because re-deriving a valid hash
-- requires re-writing every later row in sequence.
--
-- Idempotent AND tolerant: the CI migration-check database does not create
-- `audit_logs` (the running schema is Sequelize-owned), so the statements are
-- wrapped in a table-existence guard. Re-running against a real database is a
-- no-op once the columns exist.

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = current_schema() AND table_name = 'audit_logs'
  ) THEN
    ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS prev_hash VARCHAR(64);
    ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS hash VARCHAR(64);
    -- Chain verification walks created_at then id; give that scan an index.
    CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at_id ON audit_logs (created_at, id);
  END IF;
END $$;
