/**
 * Canonical JSON Response Envelope (AGENTS.md §4)
 * -----------------------------------------------
 * Every helper here writes exactly ONE body shape:
 *
 *   success → { success: true,  status, message, data, timestamp }
 *   error   → { success: false, status, message, code, data: null, timestamp }
 *
 * `status` is always the HTTP status actually used, `timestamp` is an ISO-8601
 * string, and `data` is null on errors. Two additive keys are preserved for
 * backwards compatibility with existing callers: `meta` (success only, 3rd
 * positional arg — pagination cursors) and `details` (error only, field-level
 * validation output). Helpers never write a second response once headers have
 * been sent.
 *
 * Legacy helper names (`sendSuccess`, `sendError`, …) are kept as aliases so
 * route files do not have to be rewritten.
 */

/** HTTP status → default success message. */
const SUCCESS_MESSAGES = {
  200: 'OK',
  201: 'Created',
  202: 'Accepted',
};

const timestamp = () => new Date().toISOString();

/**
 * Write a success envelope.
 *
 * @param {import('express').Response} res - Express response
 * @param {*} [data=null] - Payload (null when there is nothing to return)
 * @param {object} [meta] - Optional pagination/meta block (additive key)
 * @param {number} [status=200] - HTTP status to send
 * @param {string} [message] - Optional human-readable message
 * @returns {import('express').Response} the same response
 */
export const ok = (res, data = null, meta, status = 200, message = null) => {
  if (res.headersSent) return res;
  const body = {
    success: true,
    status,
    message: message || SUCCESS_MESSAGES[status] || 'OK',
    data,
    timestamp: timestamp(),
  };
  if (meta !== undefined && meta !== null) body.meta = meta;
  return res.status(status).json(body);
};

/**
 * Write a 201 success envelope.
 *
 * @param {import('express').Response} res - Express response
 * @param {*} [data=null] - Created resource
 * @param {object} [meta] - Optional meta block
 * @returns {import('express').Response} the same response
 */
export const created = (res, data = null, meta) => ok(res, data, meta, 201, 'Created');

/**
 * Write the canonical error envelope.
 *
 * @param {import('express').Response} res - Express response
 * @param {string} code - Machine-readable error code (e.g. 'NOT_FOUND')
 * @param {string} message - Safe, user-facing message
 * @param {number} [status=400] - HTTP status to send
 * @param {object|Array|null} [details=null] - Optional field-level details
 * @returns {import('express').Response} the same response
 */
export const fail = (res, code, message, status = 400, details = null) => {
  if (res.headersSent) return res;
  const body = {
    success: false,
    status,
    message,
    code,
    data: null,
    timestamp: timestamp(),
  };
  if (details) body.details = details;
  return res.status(status).json(body);
};

// ── Backwards-compatible aliases (same signatures as before) ────────────────
export const sendSuccess = ok;
export const sendError = fail;

export const sendNotFound = (res, resource = 'Resource') =>
  fail(res, 'NOT_FOUND', `${resource} not found`, 404);

export const sendValidationError = (res, details = null) =>
  fail(res, 'VALIDATION_ERROR', 'Validation failed', 422, details);

export const sendUnauthorized = (res, message = 'Unauthorized') =>
  fail(res, 'UNAUTHORIZED', message, 401);

export const sendForbidden = (res, message = 'Forbidden') =>
  fail(res, 'FORBIDDEN', message, 403);

export const sendServerError = (res, message = 'Internal Server Error', details = null) =>
  fail(res, 'INTERNAL_ERROR', message, 500, details);

export default {
  ok,
  created,
  fail,
  sendSuccess,
  sendError,
  sendNotFound,
  sendValidationError,
  sendUnauthorized,
  sendForbidden,
  sendServerError,
};
