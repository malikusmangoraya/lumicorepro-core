import { describe, it, expect } from 'vitest';
import {
  extractTables,
  extractForeignKeys,
  extractIndexes,
  validateSchema,
  mergeSchemas,
  validateMergedSchema,
  CORE_ECOMMERCE_TABLES,
} from '../../utils/schemaValidator';

const GOOD_SCHEMA = `
  CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT);
  CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT REFERENCES users(id));
  CREATE TABLE order_items (id SERIAL PRIMARY KEY, order_id INT REFERENCES orders(id));
  CREATE INDEX idx_orders_user ON orders(user_id);
`;

describe('schemaValidator extraction', () => {
  it('extracts unique, lowercased table names', () => {
    const sql = `
      CREATE TABLE Users (id INT);
      CREATE TABLE IF NOT EXISTS orders (id INT);
      CREATE TABLE users (id INT);
    `;
    expect(extractTables(sql)).toEqual(['users', 'orders']);
  });

  it('extracts foreign key targets', () => {
    expect(extractForeignKeys(GOOD_SCHEMA)).toEqual(['users', 'orders']);
  });

  it('extracts index names', () => {
    expect(extractIndexes(GOOD_SCHEMA)).toEqual(['idx_orders_user']);
  });
});

describe('validateSchema', () => {
  it('accepts a coherent schema', () => {
    const result = validateSchema(GOOD_SCHEMA);
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
    expect(result.tableCount).toBe(3);
  });

  it('rejects empty or non-string input', () => {
    expect(validateSchema('').valid).toBe(false);
    expect(validateSchema(null).valid).toBe(false);
    expect(validateSchema(42).valid).toBe(false);
  });

  it('errors when there is no CREATE TABLE', () => {
    const result = validateSchema('SELECT 1;');
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toMatch(/no CREATE TABLE/i);
  });

  it('enforces required tables', () => {
    const result = validateSchema(GOOD_SCHEMA, { requiredTables: ['users', 'payments'] });
    expect(result.valid).toBe(false);
    expect(result.errors.join(' ')).toMatch(/payments/);
  });

  it('warns on foreign keys to undefined tables', () => {
    const sql = 'CREATE TABLE orders (id INT, uid INT REFERENCES users(id));';
    const result = validateSchema(sql);
    expect(result.warnings.join(' ')).toMatch(/undefined table: users/);
  });

  it('warns when many tables have no indexes', () => {
    const sql = `
      CREATE TABLE a (id INT); CREATE TABLE b (id INT);
      CREATE TABLE c (id INT); CREATE TABLE d (id INT);
    `;
    expect(validateSchema(sql).warnings.join(' ')).toMatch(/indexes/i);
  });
});

describe('merge helpers', () => {
  it('mergeSchemas skips falsy sections', () => {
    const merged = mergeSchemas(['CREATE TABLE a (id INT);', null, 'CREATE TABLE b (id INT);']);
    expect(merged).toContain('CREATE TABLE a');
    expect(merged).toContain('CREATE TABLE b');
    expect(merged.match(/MERGED SECTION/g)).toHaveLength(1);
  });

  it('validateMergedSchema checks the combined result', () => {
    const result = validateMergedSchema(
      ['CREATE TABLE users (id INT);', 'CREATE TABLE orders (id INT);'],
      ['users', 'orders']
    );
    expect(result.valid).toBe(true);
    expect(result.tableCount).toBe(2);
  });

  it('exposes core ecommerce tables', () => {
    expect(CORE_ECOMMERCE_TABLES).toContain('orders');
    expect(CORE_ECOMMERCE_TABLES).toContain('cart_items');
  });
});
