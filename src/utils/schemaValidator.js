/**
 * Database schema validation utilities.
 * Validates SQL schema integrity: tables, foreign keys, indexes.
 */

const TABLE_PATTERN = /CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)/gi;
const FK_PATTERN = /REFERENCES\s+([a-zA-Z0-9_]+)\s*\(/gi;
const INDEX_PATTERN = /CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)/gi;

export function extractTables(sql) {
  const tables = [];
  let match;
  const re = new RegExp(TABLE_PATTERN.source, TABLE_PATTERN.flags);
  while ((match = re.exec(sql)) !== null) {
    tables.push(match[1].toLowerCase());
  }
  return [...new Set(tables)];
}

export function extractForeignKeys(sql) {
  const refs = [];
  let match;
  const re = new RegExp(FK_PATTERN.source, FK_PATTERN.flags);
  while ((match = re.exec(sql)) !== null) {
    refs.push(match[1].toLowerCase());
  }
  return refs;
}

export function extractIndexes(sql) {
  const indexes = [];
  let match;
  const re = new RegExp(INDEX_PATTERN.source, INDEX_PATTERN.flags);
  while ((match = re.exec(sql)) !== null) {
    indexes.push(match[1].toLowerCase());
  }
  return indexes;
}

export function validateSchema(sql, options = {}) {
  const errors = [];
  const warnings = [];

  if (!sql || typeof sql !== 'string') {
    return { valid: false, errors: ['Schema SQL is empty or invalid'], warnings: [] };
  }

  if (!/CREATE\s+TABLE/i.test(sql)) {
    errors.push('Schema contains no CREATE TABLE statements');
  }

  const tables = extractTables(sql);
  const tableSet = new Set(tables);
  const foreignKeys = extractForeignKeys(sql);
  const indexes = extractIndexes(sql);

  for (const ref of foreignKeys) {
    if (!tableSet.has(ref)) {
      warnings.push(`Foreign key references undefined table: ${ref}`);
    }
  }

  const requiredTables = options.requiredTables || [];
  for (const req of requiredTables) {
    if (!tableSet.has(req.toLowerCase())) {
      errors.push(`Missing required table: ${req}`);
    }
  }

  if (tables.length > 3 && indexes.length === 0) {
    warnings.push('Consider adding indexes for frequently queried columns');
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    tables,
    foreignKeys,
    indexes,
    tableCount: tables.length,
  };
}

export function mergeSchemas(schemas) {
  return schemas.filter(Boolean).join('\n\n-- --- MERGED SECTION ---\n\n');
}

export function validateMergedSchema(schemas, requiredTables = []) {
  const merged = mergeSchemas(schemas);
  return validateSchema(merged, { requiredTables });
}

export const CORE_ECOMMERCE_TABLES = [
  'users',
  'products',
  'categories',
  'carts',
  'cart_items',
  'orders',
  'order_items',
];

export const CORE_SAAS_TABLES = ['users', 'plans', 'subscriptions', 'invoices'];
