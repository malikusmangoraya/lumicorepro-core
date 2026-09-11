/**
 * Apply the idempotent supporting indexes (database/schemas/indexes.sql)
 * to the configured PostgreSQL database. Safe to re-run.
 *
 * Usage: node scripts/apply-indexes.js
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const sqlFile = path.join(__dirname, '..', '..', 'database', 'schemas', 'indexes.sql');

const databaseUrl =
  process.env.DATABASE_URL ||
  `postgres://${process.env.DB_USER || 'postgres'}:${process.env.DB_PASSWORD || 'postgres'}@${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || 5432}/${process.env.DB_NAME || 'lumicorepro'}`;

async function main() {
  const sql = fs.readFileSync(sqlFile, 'utf8');
  const client = new pg.Client({ connectionString: databaseUrl });
  await client.connect();
  try {
    await client.query(sql);
    console.log('Indexes applied (idempotent — already-existing indexes skipped).');
  } finally {
    await client.end();
  }
}

main().catch((err) => {
  console.error(`Failed to apply indexes: ${err.message}`);
  process.exit(1);
});