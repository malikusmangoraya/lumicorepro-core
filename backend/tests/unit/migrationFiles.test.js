import { describe, it, expect } from '@jest/globals';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const migrationsDir = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
  '..',
  '..',
  'database',
  'migrations'
);

/**
 * The migration runner splits files on semicolons and applies the fragments as
 * independent statements. Syntax that embeds a semicolon inside a comment or
 * dollar-quoted body would silently become broken SQL, so the file contract is
 * tested here instead of against a live database.
 */
function statementsFor(file) {
  const executable = fs
    .readFileSync(path.join(migrationsDir, file), 'utf8')
    .split('\n')
    .filter((line) => !line.trim().startsWith('--'))
    .join('\n');
  return executable
    .split(';')
    .map((statement) => statement.trim())
    .filter(Boolean);
}

describe('Migration file contract', () => {
  it('numbers migrations and ends each statement with a semicolon', () => {
    const files = fs
      .readdirSync(migrationsDir)
      .filter((file) => /^\d{3}__.*\.sql$/.test(file))
      .sort();

    expect(files).toContain('004__postgres_integer_foreign_keys.up.sql');
    expect(files).toContain('004__postgres_integer_foreign_keys.down.sql');
    for (const file of files) {
      const raw = fs.readFileSync(path.join(migrationsDir, file), 'utf8').trim();
      expect(raw.endsWith(';')).toBe(true);
      expect(statementsFor(file).length).toBeGreaterThan(0);
    }
  });

  it('pairs the tenant migrations with rollbacks', () => {
    for (const version of ['003__multi_tenant_scoping', '004__postgres_integer_foreign_keys']) {
      expect(fs.existsSync(path.join(migrationsDir, `${version}.up.sql`))).toBe(true);
      expect(fs.existsSync(path.join(migrationsDir, `${version}.down.sql`))).toBe(true);
    }
  });

  it('converges foreign keys onto Postgres-native integers', () => {
    const up = statementsFor('004__postgres_integer_foreign_keys.up.sql').join('\n');
    const down = statementsFor('004__postgres_integer_foreign_keys.down.sql').join('\n');

    for (const table of ['products', 'orders', 'reviews', 'carts', 'payments']) {
      expect(up).toContain(`ALTER TABLE ${table} ALTER COLUMN org_id TYPE INTEGER`);
      expect(up).toContain(`fk_${table}_org`);
      expect(down).toContain(`ALTER TABLE ${table} ALTER COLUMN org_id TYPE BIGINT`);
    }
    expect(up).toContain('ALTER TABLE users ALTER COLUMN current_org_id TYPE INTEGER');
    expect(up).not.toContain('UNSIGNED');
    expect(down).toContain('ALTER TABLE users DROP COLUMN IF EXISTS current_org_id');
    expect(down).toContain('ALTER TABLE organizations DROP COLUMN IF EXISTS owner_id');
  });
});
