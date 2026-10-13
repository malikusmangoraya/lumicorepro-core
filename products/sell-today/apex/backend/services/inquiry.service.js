'use strict';

/**
 * Inquiry domain service.
 *
 * Responsibilities:
 *  - validate a lead's contact data and record privacy consent explicitly
 *  - bind `user_id` from the verified session only (never from the payload)
 *  - keep a repeat form submission from creating a second lead
 *  - scope "my enquiries" strictly to the caller
 *
 * Only active vehicles can be enquired about, so a draft listing cannot be
 * discovered by probing the enquiry endpoint.
 */
const Vehicle = require('../models/Vehicle');
const Inquiry = require('../models/Inquiry');

const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 100;
const MAX_PAGE = 10000;
const MIN_NAME = 2;
const MAX_NAME = 120;
const MAX_MESSAGE = Inquiry.MAX_MESSAGE;
const MIN_MESSAGE = Inquiry.MIN_MESSAGE;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

const ADMIN_FILTERS = ['status', 'vehicleId', 'page', 'limit'];

class InquiryError extends Error {
  constructor(message, status, errors = []) {
    super(message);
    this.name = 'InquiryError';
    this.status = status;
    this.errors = errors;
  }
}

class InquiryValidationError extends InquiryError {
  constructor(message, errors = []) {
    super(message, 400, errors);
    this.name = 'InquiryValidationError';
  }
}

class InquiryNotFoundError extends InquiryError {
  constructor(message = 'Enquiry not found') {
    super(message, 404, []);
    this.name = 'InquiryNotFoundError';
  }
}

const fail = (field, message) => {
  throw new InquiryValidationError('Invalid enquiry', [{ field, message }]);
};

function asText(value, field, { min = 1, max = Infinity, required = true } = {}) {
  if (value === undefined || value === null || value === '') {
    if (required) fail(field, `${field} is required`);
    return null;
  }
  if (typeof value !== 'string') fail(field, `${field} must be text`);
  const trimmed = value.trim();
  if (!trimmed) {
    if (required) fail(field, `${field} is required`);
    return null;
  }
  if (trimmed.length < min) fail(field, `${field} must be at least ${min} characters`);
  if (trimmed.length > max) fail(field, `${field} must be ${max} characters or fewer`);
  return trimmed;
}

function asEmail(value) {
  const email = asText(value, 'email', { max: 160 }).toLowerCase();
  if (!EMAIL_PATTERN.test(email)) fail('email', 'email must be a valid address');
  return email;
}

function asPositiveId(value, field) {
  if (value === undefined || value === null || value === '') return null;
  if (typeof value === 'object') fail(field, `${field} must be a single id`);
  const num = Number(String(value).trim());
  if (!Number.isInteger(num) || num < 1) fail(field, `${field} must be a positive whole number`);
  return num;
}

function asPagination(raw = {}) {
  const read = (value, field, fallback, min, max) => {
    if (value === undefined) return fallback;
    if (typeof value === 'object') fail(field, `${field} must be a single number`);
    const num = Number(String(value).trim());
    if (!Number.isInteger(num)) fail(field, `${field} must be a whole number`);
    if (num < min) fail(field, `${field} must be at least ${min}`);
    if (num > max) fail(field, `${field} must be at most ${max}`);
    return num;
  };
  return {
    page: read(raw.page, 'page', 1, 1, MAX_PAGE),
    limit: read(raw.limit, 'limit', DEFAULT_LIMIT, 1, MAX_LIMIT),
  };
}

/**
 * Record an enquiry.
 *
 * @param {object} payload request body
 * @param {{userId?: number|null}} [session] verified caller, when signed in
 * @returns {Promise<{inquiry: object, created: boolean}>} `created` is false for
 *   an idempotent replay of a submission already stored.
 */
async function createInquiry(payload = {}, { userId = null } = {}) {
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new InquiryValidationError('Enquiry payload must be an object', [
      { field: 'body', message: 'body must be an object' },
    ]);
  }

  // Consent is checked before anything else: without it there is nothing to store.
  const consent =
    payload.consent_given === true ||
    payload.consentGiven === true ||
    payload.consent === true;
  if (!consent) {
    if (
      payload.consent_given !== undefined &&
      typeof payload.consent_given !== 'boolean'
    ) {
      fail('consent_given', 'consent_given must be true or false');
    }
    fail('consent_given', 'privacy consent is required before an enquiry can be sent');
  }

  const data = {
    name: asText(payload.name, 'name', { min: MIN_NAME, max: MAX_NAME }),
    email: asEmail(payload.email),
    phone: asText(payload.phone, 'phone', { max: 40, required: false }),
    message: asText(payload.message, 'message', { min: MIN_MESSAGE, max: MAX_MESSAGE }),
    locale: asText(payload.locale, 'locale', { max: 10, required: false }),
    consent_given: true,
    consent_at: new Date(),
    // The owner always comes from the verified session. A payload-supplied
    // user id is ignored, so a lead cannot be attributed to another account.
    user_id: asPositiveId(userId, 'user_id'),
  };

  const idempotencyKey = asText(
    payload.idempotency_key !== undefined ? payload.idempotency_key : payload.idempotencyKey,
    'idempotency_key',
    { max: 80, required: false }
  );
  if (idempotencyKey) data.idempotency_key = idempotencyKey;

  const vehicleId = asPositiveId(
    payload.vehicleId !== undefined ? payload.vehicleId : payload.vehicle_id,
    'vehicleId'
  );
  if (vehicleId) {
    const vehicle = await Vehicle.findOne({
      where: { id: vehicleId, status: Vehicle.PUBLIC_STATUS },
    });
    if (!vehicle) fail('vehicleId', 'that vehicle is not available for enquiries');
    data.vehicle_id = vehicle.id;
  }

  if (idempotencyKey) {
    const existing = await Inquiry.findOne({ where: { idempotency_key: idempotencyKey } });
    if (existing) {
      const sameSender =
        (existing.user_id || null) === (data.user_id || null) && existing.email === data.email;
      if (!sameSender) fail('idempotency_key', 'idempotency_key has already been used');
      return { inquiry: existing.toJSON(), created: false };
    }
  }

  try {
    const inquiry = await Inquiry.create(data);
    return { inquiry: inquiry.toJSON(), created: true };
  } catch (err) {
    // Two concurrent identical submissions: the unique index wins the race and
    // the loser returns the row that was actually stored.
    if (err && err.name === 'SequelizeUniqueConstraintError' && data.idempotency_key) {
      const existing = await Inquiry.findOne({ where: { idempotency_key: data.idempotency_key } });
      if (existing) return { inquiry: existing.toJSON(), created: false };
    }
    if (err && err.name === 'SequelizeValidationError') {
      throw new InquiryValidationError(
        'Enquiry failed validation',
        (err.errors || []).map((e) => ({ field: e.path, message: e.message }))
      );
    }
    throw err;
  }
}

/** Enquiries belonging to the caller only. */
async function listOwnInquiries(userId, raw = {}) {
  const ownerId = asPositiveId(userId, 'userId');
  if (!ownerId) {
    throw new InquiryValidationError('A signed-in account is required', [
      { field: 'userId', message: 'sign in to view your enquiries' },
    ]);
  }
  const { page, limit } = asPagination(raw);

  const where = { user_id: ownerId };
  const [total, rows] = await Promise.all([
    Inquiry.count({ where }),
    Inquiry.findAll({ where, order: [['created_at', 'DESC']], limit, offset: (page - 1) * limit }),
  ]);

  return { items: rows.map((row) => row.toJSON()), page, limit, total, hasMore: page * limit < total };
}

/** Staff queue across every buyer. */
async function listAdminInquiries(raw = {}) {
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    fail('query', 'query must be an object');
  }
  for (const key of Object.keys(raw)) {
    if (!ADMIN_FILTERS.includes(key)) fail(key, `${key} is not a supported filter`);
  }

  const { page, limit } = asPagination(raw);
  const where = {};

  if (raw.status !== undefined) {
    const status = asText(raw.status, 'status', { max: 24 });
    if (!Inquiry.STATUSES.includes(status)) {
      fail('status', `status must be one of: ${Inquiry.STATUSES.join(', ')}`);
    }
    where.status = status;
  }
  if (raw.vehicleId !== undefined) where.vehicle_id = asPositiveId(raw.vehicleId, 'vehicleId');

  const [total, rows] = await Promise.all([
    Inquiry.count({ where }),
    Inquiry.findAll({
      where,
      order: [['created_at', 'DESC']],
      limit,
      offset: (page - 1) * limit,
      include: [{ association: 'vehicle', attributes: ['id', 'slug', 'title', 'make', 'model'] }],
    }),
  ]);

  return {
    items: rows.map((row) => row.toJSON()),
    page,
    limit,
    total,
    hasMore: page * limit < total,
  };
}

/** Move an enquiry through the staff queue. */
async function updateInquiryStatus(id, status) {
  const numericId = asPositiveId(id, 'id');
  if (!numericId) fail('id', 'id is required');

  const next = asText(status, 'status', { max: 24 });
  if (!Inquiry.STATUSES.includes(next)) {
    fail('status', `status must be one of: ${Inquiry.STATUSES.join(', ')}`);
  }

  const inquiry = await Inquiry.findByPk(numericId);
  if (!inquiry) throw new InquiryNotFoundError();

  if (inquiry.status !== next) await inquiry.update({ status: next });
  return inquiry.toJSON();
}

module.exports = {
  createInquiry,
  listOwnInquiries,
  listAdminInquiries,
  updateInquiryStatus,
  InquiryError,
  InquiryValidationError,
  InquiryNotFoundError,
  DEFAULT_LIMIT,
  MAX_LIMIT,
  ADMIN_FILTERS,
};
