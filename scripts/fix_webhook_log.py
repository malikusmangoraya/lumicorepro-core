#!/usr/bin/env python3
"""Replace the Mongoose WebhookLog model with a correct Sequelize model.

`backend/models/WebhookLog.js` was generated as a Mongoose schema, but every
other model in the project is a Sequelize model backed by PostgreSQL, and the
call sites use the Sequelize API — `WebhookLog.create({ ... })` in
`backend/routes/webhook.routes.js`. A Mongoose model has no `.create()`, so the
webhook route could only ever throw at runtime, and the `mongoose` dependency
was never even declared in package.json.

This writes the Sequelize equivalent, matching the sibling `WebhookEvent` model
exactly: same DataTypes, same table naming, same explicit timestamp columns.

Usage:
    python scripts/fix_webhook_log.py --dry-run
    python scripts/fix_webhook_log.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

MODEL = '''import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

/**
 * Audit trail of every webhook delivery attempt.
 *
 * Rows older than 30 days are removed by a periodic cleanup (see
 * `scripts/prune-webhook-logs`), which replaces the TTL index a document store
 * would have given us.
 */
class WebhookLog extends Model {}

WebhookLog.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    source: {
      type: DataTypes.STRING(100),
      allowNull: false,
    },
    event: {
      type: DataTypes.STRING(150),
      allowNull: false,
    },
    payload: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    status: {
      type: DataTypes.STRING(30),
      allowNull: false,
      defaultValue: 'received',
    },
    attempts: {
      type: DataTypes.INTEGER,
      allowNull: false,
      defaultValue: 0,
    },
    error: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    createdAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
    },
    updatedAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
    },
  },
  {
    sequelize,
    modelName: 'WebhookLog',
    tableName: 'webhook_logs',
    timestamps: true,
    indexes: [
      { fields: ['source'] },
      { fields: ['event'] },
      { fields: ['createdAt'] },
      { fields: ['source', 'event', 'createdAt'] },
    ],
  }
);

export default WebhookLog;
'''

MIGRATION = """-- Webhook delivery audit trail.
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
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    if not PRODUCTS.is_dir():
        print(f"No {PRODUCTS} directory", file=sys.stderr)
        return 2
    dirs = sorted(q for q in PRODUCTS.iterdir() if q.is_dir() and not q.name.startswith("."))
    if a.only:
        dirs = [q for q in dirs if a.only in q.name]

    changed = 0
    for d in dirs:
        model = d / "backend" / "models" / "WebhookLog.js"
        if not model.is_file():
            print(f"-- {d.name:20} no WebhookLog.js — skipped")
            continue
        current = model.read_text(encoding="utf-8", errors="replace")
        if "mongoose" not in current:
            print(f"-- {d.name:20} already Sequelize — skipped")
            continue

        sql_dir = d / "database"
        mig = sql_dir / "webhook_logs.sql"
        if not a.dry_run:
            model.write_text(MODEL, encoding="utf-8")
            sql_dir.mkdir(parents=True, exist_ok=True)
            mig.write_text(MIGRATION, encoding="utf-8")

        # Prove the rewritten model parses before claiming success.
        if not a.dry_run:
            proc = subprocess.run(
                ["node", "--experimental-vm-modules",
                 str(ROOT / "scripts" / "js_parse_check.mjs"), str(model)],
                capture_output=True, text=True, timeout=120,
            )
            if proc.returncode != 0:
                print(f"-- {d.name:20} [FAIL] rewritten model does not parse")
                print(proc.stdout[:400])
                return 1

        changed += 1
        print(f"-- {d.name:20} [ok] Mongoose model -> Sequelize (+ database/webhook_logs.sql)")

    print(f"\n=== {changed} model(s) rewritten ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())