"""Idempotent schema guards for the migrations every generated product ships.

Umzug records what it ran in ``SequelizeMeta``, but the deployed API also calls
``sequelize.sync()`` on its first request (that is what makes a cold serverless
instance serve traffic at all). So a table can exist before its migration ever
ran — and a plain ``createTable`` then dies with ``relation already exists``,
which is exactly how a redeployed product ends up unhealthy with a database it
cannot migrate.

Every generated ``up()`` therefore goes through these guards: they ask Postgres
what is already there, and only create what is missing. A migration can be run
twice, out of order relative to ``sync()``, or after a partial failure, and the
result is the same schema.

The file is named ``_guards.js`` on purpose: the generated runner globs
``migrations/00*.js``, so the helper is never picked up as a migration itself.
"""
from __future__ import annotations

from pathlib import Path

GUARD_FILENAME = "_guards.js"

MIGRATION_GUARDS_JS = """/** Migration guards — create only what Postgres does not already have.
 *
 * A generated product's schema can arrive two ways: this migration, or the
 * `sequelize.sync()` the serverless entry runs on its first cold request.
 * Whichever came first wins, and the other must become a no-op instead of an
 * `already exists` error that leaves the deployed API unable to start.
 */
'use strict';

/* Checks join the migration's own transaction when there is one, so a table this
 * migration just created is visible to the next check. `transaction: undefined`
 * means "no transaction", which is how the umzug runner calls these. */

async function tableExists(queryInterface, name, options = {}) {
  const [rows] = await queryInterface.sequelize.query(
    "SELECT to_regclass(current_schema() || '.' || :name) AS reg",
    { replacements: { name }, transaction: options.transaction },
  );
  return Boolean(rows && rows[0] && rows[0].reg);
}

async function indexExists(queryInterface, table, indexName, options = {}) {
  const [rows] = await queryInterface.sequelize.query(
    'SELECT 1 AS hit FROM pg_indexes WHERE schemaname = current_schema() '
      + 'AND tablename = :table AND indexname = :index LIMIT 1',
    { replacements: { table, index: indexName }, transaction: options.transaction },
  );
  return (rows || []).length > 0;
}

/** Index name Sequelize would generate, so a guarded retry matches the first run. */
function indexNameFor(table, columns, options = {}) {
  if (options.indexName) return options.indexName;
  const base = options.name || `${table}_${columns.join('_')}`;
  return options.unique ? `${base}_unique` : base;
}

/** Postgres reserves one namespace for tables and indexes, so a clash is 42P07
 *  for both, and a re-run racing another writer can also surface as 42P06. */
function isClash(error) {
  const code = error && error.parent && error.parent.code;
  return code === '42P07' || code === '42P06';
}

async function createTableIfMissing(queryInterface, name, attributes, options = {}) {
  if (await tableExists(queryInterface, name, options)) return false;
  try {
    await queryInterface.createTable(name, attributes, options);
  } catch (error) {
    // Another process (the first sync(), or a retried deploy) won the race. The
    // table is there, which is the state this migration wanted.
    if (isClash(error)) return false;
    throw error;
  }
  return true;
}

async function addIndexIfMissing(queryInterface, table, columns, options = {}) {
  const index = indexNameFor(table, columns, options);
  if (await indexExists(queryInterface, table, index, options)) return false;
  try {
    await queryInterface.addIndex(table, columns, { ...options, indexName: index });
  } catch (error) {
    if (isClash(error)) return false;
    throw error;
  }
  return true;
}

async function dropTableIfExists(queryInterface, name, options = {}) {
  if (!(await tableExists(queryInterface, name, options))) return false;
  await queryInterface.dropTable(name, options);
  return true;
}

module.exports = {
  tableExists,
  indexExists,
  indexNameFor,
  createTableIfMissing,
  addIndexIfMissing,
  dropTableIfExists,
};
"""


def write_migration_guards(migrations_dir: Path) -> Path:
    """Drop `_guards.js` next to the migrations, overwriting an older copy."""
    target = Path(migrations_dir)
    target.mkdir(parents=True, exist_ok=True)
    path = target / GUARD_FILENAME
    path.write_text(MIGRATION_GUARDS_JS, encoding="utf-8")
    return path
