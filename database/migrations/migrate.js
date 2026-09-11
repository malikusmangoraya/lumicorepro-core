/**
 * Database Migration Runner
 * ----------------------------------------
 * Reads numbered 003-style .sql files in migrations/ and applies them idempotently inside
 * a transaction. Tracks applied migrations in a `schema_migrations` table.
 *
 * Usage:
 *   node database/migrations/migrate.js                 # apply pending migrations
 *   node database/migrations/migrate.js --dry-run       # preview pending migrations
 *   node database/migrations/migrate.js --status        # list applied/pending
 *   node database/migrations/migrate.js --rollback      # roll back the latest migration
 *   node database/migrations/migrate.js --make "name"   # scaffold a new migration file
 *
 * File conventions:
 *   003__description.up.sql   (required — must end in a semicolon-terminated statement)
 *   003__description.down.sql (optional — used by --rollback)
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { sequelize } from '../../backend/config/database.js';
import logger from '../../backend/utils/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DRY_RUN = process.argv.includes('--dry-run');
const STATUS = process.argv.includes('--status');
const ROLLBACK = process.argv.includes('--rollback');
const MAKE_IDX = process.argv.indexOf('--make');

function listSqlFiles() {
  return fs
    .readdirSync(__dirname)
    .filter(
      (f) => /^\d{3}__.*\.sql$/.test(f) && !f.endsWith('.down.sql')
    )
    .sort();
}

function listAllSql() {
  return fs
    .readdirSync(__dirname)
    .filter((f) => /^\d{3}__.*\.sql$/.test(f))
    .sort();
}

function versionOf(file) {
  return file.replace(/\.up\.sql$/, '.sql').replace(/\.sql$/, '');
}

async function ensureMigrationsTable() {
  await sequelize.query(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version    VARCHAR(255) PRIMARY KEY,
      applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
  `);
}

async function getApplied() {
  const [rows] = await sequelize.query('SELECT version FROM schema_migrations');
  return new Set(rows.map((r) => r.version));
}

function readStatements(version, direction) {
  const upCandidates =
    direction === 'up'
      ? [`${version}.up.sql`, `${version}.sql`]
      : [`${version}.down.sql`];
  let filePath = null;
  for (const candidate of upCandidates) {
    const full = path.join(__dirname, candidate);
    if (fs.existsSync(full)) {
      filePath = full;
      break;
    }
  }
  if (!filePath) return [];
  return fs
    .readFileSync(filePath, 'utf-8')
    .split(';')
    .map((s) => s.trim())
    .filter(Boolean);
}

async function runStatementsInTx(version, direction) {
  const stmts = readStatements(version, direction);
  if (stmts.length === 0) {
    logger.info(`No ${direction === 'up' ? '' : 'down '}statements for ${version} (skipping).`);
    return stmts.length;
  }

  let appliedIn = 0;
  await sequelize.transaction(async (t) => {
    for (const stmt of stmts) {
      await sequelize.query(stmt, { transaction: t });
      appliedIn++;
    }
  });
  return appliedIn;
}

async function makeMigration(name) {
  const safe = String(name || 'name')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '');
  const dir = __dirname;
  const last = fs
    .readdirSync(dir)
    .filter((f) => /^\d{3}__.*\.sql$/.test(f) || /^\d{3}__.*\.up\.sql$/.test(f))
    .sort()
    .pop();

  const version = last
    ? String(parseInt(last.slice(0, 3), 10) + 1).padStart(3, '0')
    : '001';
  const up = path.join(dir, `${version}__${safe}.up.sql`);
  const down = path.join(dir, `${version}__${safe}.down.sql`);

  if (fs.existsSync(up)) {
    logger.error(`Migration already exists: ${up}`);
    process.exit(1);
  }
  fs.writeFileSync(
    up,
    `-- ${version}: ${safe}\nBEGIN;\n\nCOMMIT;\n`
  );
  fs.writeFileSync(
    down,
    `-- ${version}: ${safe} (rollback)\nBEGIN;\n\nCOMMIT;\n`
  );
  logger.info(`Created ${up}`);
  logger.info(`Created ${down}`);
}

async function printStatus() {
  let applied = new Set();
  try {
    await ensureMigrationsTable();
    applied = await getApplied();
  } catch {
    // DB offline — show migration files only
  }
  const files = listSqlFiles().map((f) => f.replace('.sql', ''));
  logger.info('Migration status:');
  if (files.length === 0) logger.info('  (no migrations found)');
  for (const version of files) {
    const mark = applied.has(version) ? 'applied' : 'pending';
    logger.info(`  ${mark === 'applied' ? '✓' : '·'} ${version} (${mark})`);
  }
}

async function migrate() {
  let applied;
  if (DRY_RUN || STATUS) {
    applied = new Set();
  } else {
    await ensureMigrationsTable();
    applied = await getApplied();
  }

  const files = listSqlFiles().map(versionOf);
  if (DRY_RUN || STATUS) {
    for (const version of files) {
      if (applied.has(version)) continue;
      const stmts = readStatements(version, 'up');
      logger.info(
        `[${DRY_RUN ? 'dry-run' : 'status'}] Would apply ${version} (${stmts.length} statements)`
      );
    }
    if (DRY_RUN) logger.info('Dry run complete — nothing changed.');
    return;
  }

  let count = 0;
  for (const version of files) {
    if (applied.has(version)) continue;
    try {
      logger.info(`Applying migration ${version} ...`);
      const appliedIn = await runStatementsInTx(version, 'up');
      await sequelize.query('INSERT INTO schema_migrations (version) VALUES (:v)', {
        replacements: { v: version },
      });
      logger.info(`Migration ${version} applied successfully (${appliedIn} statements).`);
      count++;
    } catch (err) {
      logger.error(`Migration ${version} failed: ${err.message}`);
      logger.error('Transaction rolled back — database unchanged.');
      process.exit(1);
    }
  }

  if (count === 0) logger.info('Database is up to date.');
  logger.info(`${count} migration(s) applied.`);
}

async function rollback() {
  await ensureMigrationsTable();
  const [[latest]] = await sequelize.query(
    'SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1'
  );
  if (!latest) {
    logger.info('Nothing to roll back.');
    return;
  }
  logger.info(`Rolling back ${latest.version} ...`);
  try {
    const rolled = await runStatementsInTx(latest.version, 'down');
    await sequelize.query('DELETE FROM schema_migrations WHERE version = :v', {
      replacements: { v: latest.version },
    });
    logger.info(`Rolled back ${latest.version} (${rolled} down statements).`);
  } catch (err) {
    logger.error(`Rollback failed: ${err.message}`);
    process.exit(1);
  }
}

async function main() {
  if (MAKE_IDX !== -1) {
    await makeMigration(process.argv[MAKE_IDX + 1]);
    return;
  }
  if (STATUS) {
    await printStatus();
    return;
  }
  if (ROLLBACK) {
    await rollback();
    return;
  }
  await migrate();
}

main()
  .then(() => process.exit(0))
  .catch((err) => {
    logger.error(`Migration failed: ${err.message}`);
    process.exit(1);
  });

export default migrate;