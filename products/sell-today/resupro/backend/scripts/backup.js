'use strict';
/**
 * Write a compressed PostgreSQL dump to backend/backups/.
 *
 * Usage:
 *   node scripts/backup.js
 *   docker compose exec backend node scripts/backup.js
 *
 * Requires DATABASE_URL with a postgresql:// connection string and a
 * pg_dump binary in PATH. Never prints the connection string.
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function main() {
  const url = process.env.DATABASE_URL || '';
  if (!url.startsWith('postgresql://') && !url.startsWith('postgres://')) {
    console.error('[backup] DATABASE_URL must be a postgresql:// connection string.');
    process.exit(2);
  }
  const dir = path.join(__dirname, '..', 'backups');
  fs.mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const out = path.join(dir, `backup-${stamp}.dump`);
  const r = spawnSync('pg_dump', ['--format=custom', '--file', out, url], { stdio: 'inherit' });
  if (r.status !== 0) {
    console.error('[backup] pg_dump failed. Is PostgreSQL client installed and DATABASE_URL reachable?');
    process.exit(r.status || 1);
  }
  console.log(`[backup] wrote ${out}`);
  console.log('[backup] restore with: pg_restore --clean --if-exists -d "$DATABASE_URL" <file>');
}

if (require.main === module) main();
module.exports = { main };
