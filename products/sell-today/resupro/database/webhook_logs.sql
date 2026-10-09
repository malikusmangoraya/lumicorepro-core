-- Webhook delivery audit trail.
--
-- Created as PostgreSQL/Sequelize to match every other model in the project.
-- The document-store version of this model was never usable: the call sites
-- use the Sequelize API and the dependency was not declared.
CREATE TABLE IF NOT EXISTS webhook_logs (
  id         SERIAL PRIMARY KEY,
  source     VARCHAR(100) NOT NULL,
  event      VARCHAR(150) NOT NULL,
  payload    TEXT,
  status     VARCHAR(30)  NOT NULL DEFAULT 'received',
  attempts   INTEGER      NOT NULL DEFAULT 0,
  error      TEXT,
  created_at TIMESTAMP    NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhook_logs_source   ON webhook_logs (source);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_event    ON webhook_logs (event);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_created  ON webhook_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_combo    ON webhook_logs (source, event, created_at);
