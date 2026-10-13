'use strict';

/**
 * Vehicle domain service.
 *
 * Owns every rule about *which* vehicles the public may see and *how* filters
 * are turned into a query. Routes stay thin: they authenticate, call in here,
 * and translate the typed errors below into HTTP status codes.
 *
 * Design notes:
 *  - Filters are whitelisted. An unknown key, a malformed bound or an
 *    out-of-range pagination value raises `VehicleValidationError` (400) instead
 *    of degrading into an unbounded scan.
 *  - Public reads are hard-scoped to `status = 'active'`. No parameter can widen
 *    that, which is why the status filter is rejected outright on the public path.
 *  - Withdrawal is a state change, never a row delete: inquiry and reservation
 *    history must outlive the listing.
 */
const { Op } = require('sequelize');
const Vehicle = require('../models/Vehicle');

const DEFAULT_LIMIT = 12;
const MAX_LIMIT = 60;
const MAX_PAGE = 10000;
const MAX_Q_LENGTH = 80;
const MAX_SHORT_TEXT = 120;

/** Query parameters the listing endpoint understands. */
const ALLOWED_FILTERS = [
  'q', 'make', 'model', 'yearMin', 'yearMax', 'priceMin', 'priceMax', 'currency',
  'mileageMax', 'mileageUnit', 'bodyStyle', 'fuelType', 'transmission', 'country',
  'status', 'sort', 'page', 'limit',
];

/** Fields an admin may write. Anything else (including `id`) is dropped. */
const WRITABLE_FIELDS = [
  'slug', 'make', 'model', 'year', 'title', 'description', 'price', 'currency',
  'mileage', 'mileage_unit', 'body_style', 'fuel_type', 'transmission',
  'location_country', 'location_region', 'status', 'media',
  'inspection_references', 'provenance_verified', 'condition_notes',
  'condition_report_url', 'vin',
];

/** camelCase API aliases → snake_case columns. */
const FIELD_ALIASES = {
  mileageUnit: 'mileage_unit',
  bodyStyle: 'body_style',
  fuelType: 'fuel_type',
  locationCountry: 'location_country',
  locationRegion: 'location_region',
  inspectionReferences: 'inspection_references',
  provenanceVerified: 'provenance_verified',
  conditionNotes: 'condition_notes',
  conditionReportUrl: 'condition_report_url',
};

const COUNTRY_PATTERN = /^[A-Z]{2}$/;

class VehicleError extends Error {
  constructor(message, status, errors = []) {
    super(message);
    this.name = 'VehicleError';
    this.status = status;
    this.errors = errors;
  }
}

class VehicleValidationError extends VehicleError {
  constructor(message, errors = []) {
    super(message, 400, errors);
    this.name = 'VehicleValidationError';
  }
}

class VehicleNotFoundError extends VehicleError {
  constructor(message = 'Vehicle not found') {
    super(message, 404, []);
    this.name = 'VehicleNotFoundError';
  }
}

class VehicleConflictError extends VehicleError {
  constructor(message, errors = []) {
    super(message, 409, errors);
    this.name = 'VehicleConflictError';
  }
}

const fail = (field, message) => {
  throw new VehicleValidationError(`Invalid vehicle query: ${field}`, [{ field, message }]);
};

/** Escape LIKE wildcards so user text cannot widen a match. */
const escapeLike = (value) => String(value).replace(/[\\%_]/g, (ch) => `\\${ch}`);

function requireString(raw, field, { max = MAX_SHORT_TEXT, pattern, patternMessage, upperCase = false } = {}) {
  if (typeof raw !== 'string') fail(field, `${field} must be a single text value`);
  const trimmed = raw.trim();
  if (!trimmed) fail(field, `${field} cannot be empty`);
  if (trimmed.length > max) fail(field, `${field} must be ${max} characters or fewer`);
  const value = upperCase ? trimmed.toUpperCase() : trimmed;
  if (pattern && !pattern.test(value)) fail(field, patternMessage || `${field} has an invalid format`);
  return value;
}

function requireNumber(raw, field, { integer = false, min, max } = {}) {
  if (typeof raw !== 'string' && typeof raw !== 'number') {
    fail(field, `${field} must be a single numeric value`);
  }
  const text = String(raw).trim();
  if (!text) fail(field, `${field} cannot be empty`);
  const value = Number(text);
  if (!Number.isFinite(value)) fail(field, `${field} must be a number`);
  if (integer && !Number.isInteger(value)) fail(field, `${field} must be a whole number`);
  if (min !== undefined && value < min) fail(field, `${field} must be at least ${min}`);
  if (max !== undefined && value > max) fail(field, `${field} must be at most ${max}`);
  return value;
}

/**
 * Validate and normalise a raw query object into a Sequelize `where` clause
 * plus pagination/sort settings.
 *
 * @param {object} raw Express `req.query`
 * @param {{includeInactive?: boolean}} [options] admin mode only
 * @returns {{where: object, page: number, limit: number, sort: string, includeInactive: boolean}}
 */
function normalizeListFilters(raw = {}, { includeInactive = false } = {}) {
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    fail('query', 'query must be an object');
  }

  for (const key of Object.keys(raw)) {
    if (!ALLOWED_FILTERS.includes(key)) fail(key, `${key} is not a supported filter`);
  }

  const where = {};
  let page = 1;
  let limit = DEFAULT_LIMIT;
  let sort = 'newest';

  if (raw.q !== undefined) {
    const q = requireString(raw.q, 'q', { max: MAX_Q_LENGTH });
    const like = { [Op.like]: `%${escapeLike(q)}%` };
    where[Op.or] = [{ make: like }, { model: like }, { title: like }, { location_region: like }];
  }

  if (raw.make !== undefined) where.make = requireString(raw.make, 'make', { max: 80 });
  if (raw.model !== undefined) where.model = requireString(raw.model, 'model', { max: 120 });

  if (raw.yearMin !== undefined || raw.yearMax !== undefined) {
    const year = {};
    if (raw.yearMin !== undefined) year[Op.gte] = requireNumber(raw.yearMin, 'yearMin', { integer: true, min: 1900 });
    if (raw.yearMax !== undefined) year[Op.lte] = requireNumber(raw.yearMax, 'yearMax', { integer: true, min: 1900 });
    if (year[Op.gte] !== undefined && year[Op.lte] !== undefined && year[Op.gte] > year[Op.lte]) {
      fail('yearMin', 'yearMin cannot be greater than yearMax');
    }
    where.year = year;
  }

  if (raw.priceMin !== undefined || raw.priceMax !== undefined) {
    const price = {};
    if (raw.priceMin !== undefined) price[Op.gte] = requireNumber(raw.priceMin, 'priceMin', { min: 0 });
    if (raw.priceMax !== undefined) price[Op.lte] = requireNumber(raw.priceMax, 'priceMax', { min: 0 });
    if (price[Op.gte] !== undefined && price[Op.lte] !== undefined && price[Op.gte] > price[Op.lte]) {
      fail('priceMin', 'priceMin cannot be greater than priceMax');
    }
    where.price = price;
  }

  if (raw.currency !== undefined) {
    const currency = requireString(raw.currency, 'currency', {
      max: 3,
      upperCase: true,
      pattern: /^[A-Z]{3}$/,
      patternMessage: 'currency must be a three-letter ISO 4217 code',
    });
    if (!Vehicle.SUPPORTED_CURRENCIES.includes(currency)) {
      fail('currency', `currency ${currency} is not supported for listings`);
    }
    where.currency = currency;
  }

  if (raw.mileageMax !== undefined) {
    where.mileage = { [Op.lte]: requireNumber(raw.mileageMax, 'mileageMax', { integer: true, min: 0 }) };
  }

  if (raw.mileageUnit !== undefined) {
    const unit = requireString(raw.mileageUnit, 'mileageUnit', { max: 2 }).toLowerCase();
    if (!Vehicle.MILEAGE_UNITS.includes(unit)) fail('mileageUnit', 'mileageUnit must be km or mi');
    where.mileage_unit = unit;
  }

  if (raw.bodyStyle !== undefined) where.body_style = requireString(raw.bodyStyle, 'bodyStyle', { max: 40 });
  if (raw.fuelType !== undefined) where.fuel_type = requireString(raw.fuelType, 'fuelType', { max: 40 });
  if (raw.transmission !== undefined) where.transmission = requireString(raw.transmission, 'transmission', { max: 40 });

  if (raw.country !== undefined) {
    where.location_country = requireString(raw.country, 'country', {
      max: 2,
      upperCase: true,
      pattern: COUNTRY_PATTERN,
      patternMessage: 'country must be a two-letter ISO 3166-1 code',
    });
  }

  if (raw.status !== undefined) {
    if (!includeInactive) {
      fail('status', 'status is not a public filter; public listings are always active');
    }
    const status = requireString(raw.status, 'status', { max: 20 });
    if (!Vehicle.STATUSES.includes(status)) fail('status', 'status is not a known listing state');
    where.status = status;
  }

  if (raw.sort !== undefined) {
    const requested = requireString(raw.sort, 'sort', { max: 30 });
    if (!Object.prototype.hasOwnProperty.call(Vehicle.SORT_OPTIONS, requested)) {
      fail('sort', `sort must be one of: ${Object.keys(Vehicle.SORT_OPTIONS).join(', ')}`);
    }
    sort = requested;
  }

  if (raw.page !== undefined) page = requireNumber(raw.page, 'page', { integer: true, min: 1, max: MAX_PAGE });
  if (raw.limit !== undefined) limit = requireNumber(raw.limit, 'limit', { integer: true, min: 1, max: MAX_LIMIT });

  return { where, page, limit, sort, includeInactive };
}

/**
 * Public/admin listing query.
 *
 * @param {object} raw query parameters
 * @param {{includeInactive?: boolean}} [options]
 */
async function listVehicles(raw = {}, options = {}) {
  const { where, page, limit, sort, includeInactive } = normalizeListFilters(raw, options);

  // The public scope is applied after validation so no filter can widen it.
  if (!includeInactive) where.status = Vehicle.PUBLIC_STATUS;

  const [total, rows] = await Promise.all([
    Vehicle.count({ where }),
    Vehicle.findAll({
      where,
      order: Vehicle.SORT_OPTIONS[sort],
      limit,
      offset: (page - 1) * limit,
    }),
  ]);

  return {
    items: rows.map((row) => row.toJSON()),
    page,
    limit,
    total,
    hasMore: page * limit < total,
    sort,
  };
}

/** Active listing by slug. Inactive or unknown slugs are indistinguishable. */
async function getPublicVehicleBySlug(slug) {
  if (typeof slug !== 'string' || !slug.trim()) {
    fail('slug', 'slug is required');
  }
  const vehicle = await Vehicle.findOne({
    where: { slug: slug.trim().toLowerCase(), status: Vehicle.PUBLIC_STATUS },
  });
  if (!vehicle) throw new VehicleNotFoundError();
  return vehicle.toJSON();
}

/** Any listing by primary key, for staff screens. */
async function getVehicleById(id) {
  const numericId = requireNumber(id, 'id', { integer: true, min: 1 });
  const vehicle = await Vehicle.findByPk(numericId);
  if (!vehicle) throw new VehicleNotFoundError();
  return vehicle.toJSON();
}

/** Reduce a payload to writable columns; drop aliases, `id` and unknown keys. */
function pickWritable(payload) {
  const data = {};
  for (const [rawKey, rawValue] of Object.entries(payload)) {
    const key = FIELD_ALIASES[rawKey] || rawKey;
    if (!WRITABLE_FIELDS.includes(key)) continue;
    data[key] = rawValue;
  }
  return data;
}

/** Turn Sequelize validation/constraint failures into typed service errors. */
function asVehicleError(err) {
  if (err && err.name === 'SequelizeValidationError') {
    return new VehicleValidationError(
      'Vehicle listing failed validation',
      (err.errors || []).map((e) => ({ field: e.path, message: e.message }))
    );
  }
  if (err && err.name === 'SequelizeUniqueConstraintError') {
    return new VehicleConflictError(
      'A vehicle with that slug already exists',
      (err.errors || []).map((e) => ({ field: e.path, message: e.message }))
    );
  }
  return err;
}

function slugify(text) {
  const base = String(text || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 160)
    .replace(/-+$/g, '');
  return base || 'vehicle';
}

/** Find the first free slug, suffixing `-2`, `-3`, … when taken. */
async function uniqueSlug(base) {
  const root = base || 'vehicle';
  let candidate = root;
  let suffix = 2;
  while (await Vehicle.count({ where: { slug: candidate } })) {
    candidate = `${root}-${suffix}`.slice(0, 160).replace(/-+$/g, '');
    suffix += 1;
    if (suffix > 500) return `${root}-${Date.now()}`.slice(0, 160);
  }
  return candidate;
}

/** Admin: create a listing. Only whitelisted fields are honoured. */
async function createVehicle(payload = {}) {
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new VehicleValidationError('Vehicle payload must be an object', [
      { field: 'body', message: 'body must be an object' },
    ]);
  }

  const data = pickWritable(payload);

  if (data.slug) {
    const requested = slugify(data.slug);
    if (await Vehicle.count({ where: { slug: requested } })) {
      throw new VehicleConflictError('A vehicle with that slug already exists', [
        { field: 'slug', message: 'slug already in use' },
      ]);
    }
    data.slug = requested;
  } else {
    // Prefer the title: it already reads as "2025 Lexus LC500", so appending
    // year/make/model to it would duplicate them in the slug.
    const slugSource =
      data.title ||
      [data.year, data.make, data.model]
        .filter((part) => part !== undefined && part !== null && part !== '')
        .join(' ');
    data.slug = await uniqueSlug(slugify(slugSource));
  }

  try {
    const created = await Vehicle.create(data);
    return created.toJSON();
  } catch (err) {
    throw asVehicleError(err);
  }
}

/** Admin: partial update. */
async function updateVehicle(id, payload = {}) {
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new VehicleValidationError('Vehicle payload must be an object', [
      { field: 'body', message: 'body must be an object' },
    ]);
  }

  const numericId = requireNumber(id, 'id', { integer: true, min: 1 });
  const vehicle = await Vehicle.findByPk(numericId);
  if (!vehicle) throw new VehicleNotFoundError();

  const data = pickWritable(payload);

  if (data.slug) {
    const requested = slugify(data.slug);
    if (requested !== vehicle.slug) {
      const clash = await Vehicle.findOne({ where: { slug: requested } });
      if (clash) {
        throw new VehicleConflictError('A vehicle with that slug already exists', [
          { field: 'slug', message: 'slug already in use' },
        ]);
      }
    }
    data.slug = requested;
  }

  if (Object.keys(data).length === 0) return vehicle.toJSON();

  try {
    await vehicle.update(data);
    return vehicle.toJSON();
  } catch (err) {
    throw asVehicleError(err);
  }
}

/**
 * Admin: withdraw a listing.
 *
 * Soft by design — the row is retained so inquiries and reservations keep
 * pointing at something real.
 */
async function withdrawVehicle(id) {
  const numericId = requireNumber(id, 'id', { integer: true, min: 1 });
  const vehicle = await Vehicle.findByPk(numericId);
  if (!vehicle) throw new VehicleNotFoundError();

  if (vehicle.status !== 'withdrawn') {
    await vehicle.update({ status: 'withdrawn' });
  }
  return vehicle.toJSON();
}

module.exports = {
  listVehicles,
  getPublicVehicleBySlug,
  getVehicleById,
  createVehicle,
  updateVehicle,
  withdrawVehicle,
  normalizeListFilters,
  slugify,
  escapeLike,
  VehicleError,
  VehicleValidationError,
  VehicleNotFoundError,
  VehicleConflictError,
  DEFAULT_LIMIT,
  MAX_LIMIT,
  MAX_PAGE,
  ALLOWED_FILTERS,
  WRITABLE_FIELDS,
};
