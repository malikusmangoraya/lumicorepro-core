/**
 * In-memory Sequelize model doubles for route-level tests.
 *
 * No PostgreSQL/sqlite driver is available offline, so these doubles implement
 * the slice of the Sequelize API the routes actually use:
 *   - `where` matching (equality, NULL / `Op.is`, `Op.or` / `Op.and`, ranges,
 *     `Op.in`, `Op.iLike`),
 *   - the paranoid default scope (rows whose soft-delete column is set are hidden
 *     unless `paranoid: false` is passed),
 *   - aggregate attributes (`fn('SUM' | 'AVG' | 'COUNT' | 'DATE' | 'TO_CHAR')`)
 *     with and without `group`,
 *   - instance `update()` / `destroy()` that mutate the stored row, so a test can
 *     assert what really happened to the data.
 *
 * Every call is recorded (`model.calls`) with the exact options object, which lets
 * a test assert on the tenant filter each query carried.
 */
import { Op } from 'sequelize';

/** Column name behind a Sequelize `col()` / string expression. */
function columnOf(expr) {
  if (typeof expr === 'string') return expr;
  if (expr && typeof expr.col === 'string') return expr.col;
  return null;
}

/** Match one column value against a Sequelize `where` value. */
function matchColumn(actual, expected) {
  if (expected === null) return actual === null || actual === undefined;
  if (expected instanceof Date) {
    return actual instanceof Date && actual.getTime() === expected.getTime();
  }
  if (typeof expected !== 'object') return String(actual) === String(expected);

  if (Op.is in expected) {
    const value = expected[Op.is];
    return value === null ? actual === null || actual === undefined : String(actual) === String(value);
  }
  if (Op.eq in expected) return matchColumn(actual, expected[Op.eq]);
  if (Op.ne in expected) return !matchColumn(actual, expected[Op.ne]);
  if (Op.gt in expected) return Number(actual) > Number(expected[Op.gt]);
  if (Op.gte in expected) return Number(actual) >= Number(expected[Op.gte]);
  if (Op.lt in expected) return Number(actual) < Number(expected[Op.lt]);
  if (Op.lte in expected) return Number(actual) <= Number(expected[Op.lte]);
  if (Op.in in expected) return expected[Op.in].some((v) => String(v) === String(actual));
  if (Op.notIn in expected) return !expected[Op.notIn].some((v) => String(v) === String(actual));
  if (Op.like in expected || Op.iLike in expected) {
    const raw = Op.like in expected ? expected[Op.like] : expected[Op.iLike];
    const pattern = String(raw).replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/%/g, '.*');
    return new RegExp(`^${pattern}$`, 'i').test(String(actual ?? ''));
  }
  return false;
}

/** Evaluate a Sequelize `where` object against a plain row. */
export function matchesWhere(row, where = {}) {
  return Reflect.ownKeys(where).every((key) => {
    const expected = where[key];
    if (key === Op.or) return expected.some((clause) => matchesWhere(row, clause));
    if (key === Op.and) return expected.every((clause) => matchesWhere(row, clause));
    return matchColumn(row[key], expected);
  });
}

/** True when the options ask for SQL aggregates (`[[fn(...), 'alias']]`). */
function isAggregateQuery(options) {
  return Array.isArray(options.attributes) && options.attributes.some((a) => Array.isArray(a));
}

/** Compute one aggregate attribute over the rows of a group. */
function evalAggregate(expr, rows) {
  const fnName = expr && expr.fn ? String(expr.fn).toUpperCase() : null;
  const args = (expr && expr.args) || [];
  const column = args.map((a) => (a && typeof a === 'object' ? a.col : null)).find(Boolean);

  if (!fnName) return rows.length ? rows[0][column] : null;
  if (fnName === 'COUNT') return rows.length;
  if (fnName === 'SUM') return rows.reduce((sum, r) => sum + Number(r[column] || 0), 0);
  if (fnName === 'AVG') {
    return rows.length ? rows.reduce((sum, r) => sum + Number(r[column] || 0), 0) / rows.length : null;
  }
  if (fnName === 'DATE') return rows.length ? String(rows[0][column]).slice(0, 10) : null;
  if (fnName === 'TO_CHAR') return rows.length ? String(rows[0][column]).slice(0, 7) : null;
  return null;
}

/** Build the projected result row(s) for an aggregate query. */
function aggregateRows(rows, options) {
  const out = {};
  for (const attr of options.attributes) {
    if (typeof attr === 'string') {
      out[attr] = rows.length ? rows[0][attr] : null;
      continue;
    }
    const [expr, alias] = attr;
    out[alias] = evalAggregate(expr, rows);
  }
  return out;
}

/** Group-key value for one `group` expression. */
function groupKeyOf(expr, row) {
  if (typeof expr === 'string') return String(row[expr]);
  const fnName = expr && expr.fn ? String(expr.fn).toUpperCase() : null;
  const args = (expr && expr.args) || [];
  const column = args.map((a) => (a && typeof a === 'object' ? a.col : null)).find(Boolean);
  const value = column ? String(row[column]) : '';
  if (fnName === 'DATE') return value.slice(0, 10);
  if (fnName === 'TO_CHAR') return value.slice(0, 7);
  return value;
}

/** Copy the requested attributes (strings, `[expr, alias]` pairs, `exclude`). */
function projectRow(row, attributes) {
  if (!attributes || Array.isArray(attributes) === false) {
    const out = { ...row };
    for (const key of (attributes && attributes.exclude) || []) delete out[key];
    return out;
  }
  const out = {};
  for (const attr of attributes) {
    if (typeof attr === 'string') out[attr] = row[attr];
  }
  return out;
}

/**
 * Create an in-memory model double.
 * @param {string} name label used in assertions
 * @param {Array<object>} rows mutable backing store
 * @param {{paranoidField?: string|null}} [options] soft-delete column
 */
export function createFakeModel(name, rows = [], { paranoidField = null } = {}) {
  let nextId = rows.reduce((max, r) => Math.max(max, Number(r.id) || 0), 0) + 1;

  const model = {
    name,
    rows,
    calls: [],
    /** Options of every call to `method` (e.g. `whereCalls('findAll')`). */
    whereCalls(method) {
      return model.calls.filter((c) => c.method === method).map((c) => c.options);
    },
  };

  const record = (method, options) => model.calls.push({ method, options });
  const visible = (options = {}) => {
    if (!paranoidField || options.paranoid === false) return rows;
    return rows.filter((r) => r[paranoidField] === null || r[paranoidField] === undefined);
  };
  const find = (options = {}) => visible(options).filter((r) => matchesWhere(r, options.where));

  /** Instance double: live row values + mutating update/destroy. */
  const wrap = (row) => {
    const instance = {
      _row: row,
      toJSON() {
        return { ...row };
      },
      async update(values, options) {
        record('update', { where: { id: row.id }, values, options });
        Object.assign(row, values);
        return instance;
      },
      async destroy(options = {}) {
        record('destroy', { where: { id: row.id }, options });
        if (paranoidField && options.force !== true) {
          row[paranoidField] = new Date();
        } else {
          const index = rows.indexOf(row);
          if (index >= 0) rows.splice(index, 1);
        }
      },
    };
    return new Proxy(instance, {
      get(target, prop) {
        if (prop in target) return target[prop];
        return row[prop];
      },
      has(target, prop) {
        return prop in target || prop in row;
      },
    });
  };

  model.findOne = async (options = {}) => {
    record('findOne', options);
    const matched = find(options);
    if (matched.length === 0) return null;
    if (isAggregateQuery(options)) return aggregateRows(matched, options);
    return options.raw ? projectRow(matched[0], options.attributes) : wrap(matched[0]);
  };

  model.findByPk = async (id, options = {}) => {
    const merged = { ...options, where: { ...(options.where || {}), id } };
    record('findByPk', merged);
    const found = find(merged)[0];
    return found ? wrap(found) : null;
  };

  model.findAll = async (options = {}) => {
    record('findAll', options);
    const matched = find(options);

    if (options.group) {
      const groups = new Map();
      for (const row of matched) {
        const key = options.group.map((g) => groupKeyOf(g, row)).join('|');
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(row);
      }
      return [...groups.values()].map((groupRows) => aggregateRows(groupRows, options));
    }

    const limited = matched.slice(options.offset || 0, options.limit ? (options.offset || 0) + options.limit : undefined);
    if (isAggregateQuery(options)) return [aggregateRows(limited, options)];
    return options.raw ? limited.map((r) => projectRow(r, options.attributes)) : limited.map(wrap);
  };

  model.findAndCountAll = async (options = {}) => {
    record('findAndCountAll', options);
    const matched = find(options);
    const start = options.offset || 0;
    const page = matched.slice(start, options.limit ? start + options.limit : undefined);
    return { count: matched.length, rows: page.map(wrap) };
  };

  model.count = async (options = {}) => {
    record('count', options);
    return find(options).length;
  };

  model.create = async (values = {}, options = {}) => {
    record('create', { values, options });
    const row = { id: nextId, ...values };
    nextId += 1;
    rows.push(row);
    return wrap(row);
  };

  model.update = async (values, options = {}) => {
    record('update', { values, options });
    const matched = find(options);
    for (const row of matched) Object.assign(row, values);
    return [matched.length];
  };

  model.destroy = async (options = {}) => {
    record('destroy', options);
    const matched = find(options);
    if (paranoidField && options.force !== true) {
      for (const row of matched) row[paranoidField] = new Date();
    } else {
      for (const row of matched) {
        const index = rows.indexOf(row);
        if (index >= 0) rows.splice(index, 1);
      }
    }
    return matched.length;
  };

  return model;
}

/** Sequelize double exposing only what the services use: `transaction` + `LOCK`. */
export function createFakeSequelize() {
  const t = { LOCK: { UPDATE: 'UPDATE' }, id: 'tx-1' };
  return {
    transaction: (callback) => Promise.resolve(callback(t)),
    _transaction: t,
  };
}

export default { createFakeModel, createFakeSequelize, matchesWhere };
