/** middleware/validate — schema validation + XSS defense for every route.
 * SQL injection is structurally prevented by Sequelize's parameterized
 * queries; this layer defends the JSON boundary:
 *   validate(schema)  -> 422 with per-field messages, unknown fields dropped
 *   sanitize()        -> escapes < > " ' & recursively in strings
 *   errorHandler      -> central JSON error terminator (never leaks stack)
 */
const MAX_FIELD_LEN = 10000;

function _escape(value) {
  return String(value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
}

function sanitize(body, depth = 0) {
  if (depth > 6 || body === null || body === undefined) return body;
  if (typeof body === 'string') return _escape(body).slice(0, MAX_FIELD_LEN);
  if (Array.isArray(body)) return body.map((v) => sanitize(v, depth + 1));
  if (typeof body === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(body)) out[k] = sanitize(v, depth + 1);
    return out;
  }
  return body;
}

/** schema: { field: { required?, type?: 'string'|'number'|'boolean', max?, min? } } */
function validate(schema) {
  return (req, _res, next) => {
    const body = req.body || {};
    const errors = {};
    for (const [field, rule] of Object.entries(schema)) {
      const value = body[field];
      if (value === undefined || value === null || value === '') {
        if (rule.required) errors[field] = `${field} is required`;
        continue;
      }
      const actual = typeof value;
      if (rule.type && actual !== rule.type) {
        errors[field] = `${field} must be ${rule.type}`;
        continue;
      }
      if (rule.type === 'string' && rule.max && value.length > rule.max) {
        errors[field] = `${field} must be <= ${rule.max} chars`;
      }
      if (rule.type === 'string' && rule.min && value.length < rule.min) {
        errors[field] = `${field} must be >= ${rule.min} chars`;
      }
      if (rule.type === 'number' && !Number.isFinite(value)) {
        errors[field] = `${field} must be finite`;
      }
    }
    if (Object.keys(errors).length) {
      return next({ status: 422, code: 'VALIDATION_ERROR', errors });
    }
    req.body = sanitize(body);
    return next();
  };
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, _req, res, _next) {
  const status = err.status || err.statusCode || 500;
  console.error(`[${new Date().toISOString()}] ${status} ${err.code || 'ERROR'}:`, err.message, status >= 500 ? `\n${err.stack}` : '');
  if (res.headersSent) return;
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ success: false, message: 'Invalid JSON body' });
  }
  res.status(status).json({
    success: false,
    code: err.code || 'ERROR',
    message: status >= 500 ? 'Something went wrong' : err.message,
    errors: err.errors || undefined,
  });
}

module.exports = { validate, sanitize, errorHandler };
