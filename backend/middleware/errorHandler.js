import logger from '../utils/logger.js';
import resp from '../utils/response.js';
import { isAppError } from '../utils/errors.js';

const { fail } = resp;

const isProduction = () => process.env.NODE_ENV === 'production';

// ── 404 handler ─────────────────────────────────────────────────────────────
// The canonical envelope is written by the helper itself — the response object
// is never re-serialized (that produced a circular-JSON "double response").
const notFound = (req, res, next) => {
  if (res.headersSent) return next();
  return fail(res, 'NOT_FOUND', `Route ${req.method} ${req.originalUrl} not found`, 404);
};

// ── Global error handler ─────────────────────────────────────────────────────
const errorHandler = (err, req, res, next) => {
  // A response has already been written (e.g. a streaming route failed midway).
  // Hand the error back to Express instead of writing a second body.
  if (res.headersSent) return next(err);

  // Explicit AppError status/code wins; otherwise fall back to res.statusCode.
  const statusCode = isAppError(err)
    ? err.statusCode
    : (res.statusCode === 200 ? 500 : res.statusCode);

  // Log error details (server-side only — never sent to the client)
  logger.error(`[${req.method}] ${req.originalUrl} — ${err.message}`, {
    stack: err.stack,
    ip: req.ip,
  });

  // ── Explicit application errors (AppError) ───────────────────────────────
  if (isAppError(err)) {
    return fail(res, err.code, err.message, statusCode, err.details || null);
  }

  // ── Sequelize: Unique constraint (e.g. duplicate email) ──────────────────
  if (err.name === 'SequelizeUniqueConstraintError') {
    const fields = err.errors?.map((e) => e.path).join(', ') || 'field';
    return fail(res, 'DUPLICATE_VALUE', `Duplicate value: ${fields} already exists`, 400);
  }

  // ── Sequelize: Validation error (model-level validators) ─────────────────
  if (err.name === 'SequelizeValidationError') {
    const details = err.errors?.map((e) => e.message) || [err.message];
    return fail(res, 'VALIDATION_ERROR', 'Validation Error', 400, details);
  }

  // ── Sequelize: Database connection error ──────────────────────────────────
  if (err.name === 'SequelizeConnectionError' || err.name === 'SequelizeConnectionRefusedError') {
    return fail(
      res,
      'DATABASE_UNAVAILABLE',
      'Database connection unavailable. Please try again shortly.',
      503,
    );
  }

  // ── Sequelize: Generic database error ────────────────────────────────────
  if (err.name?.startsWith('Sequelize')) {
    return fail(
      res,
      'DATABASE_ERROR',
      isProduction() ? 'A database error occurred' : err.message,
      500,
    );
  }

  // ── JWT errors ────────────────────────────────────────────────────────────
  if (err.name === 'JsonWebTokenError') {
    return fail(res, 'INVALID_TOKEN', 'Invalid token', 401);
  }

  if (err.name === 'TokenExpiredError') {
    return fail(res, 'TOKEN_EXPIRED', 'Token expired — please log in again', 401);
  }

  // ── Multer / file upload errors ───────────────────────────────────────────
  if (err.code === 'LIMIT_FILE_SIZE') {
    return fail(res, 'FILE_TOO_LARGE', 'File too large. Maximum allowed size is 10 MB.', 413);
  }

  if (err.code === 'LIMIT_UNEXPECTED_FILE') {
    return fail(res, 'UNEXPECTED_FILE', 'Unexpected file field in upload request.', 400);
  }

  // ── Stripe payment errors ─────────────────────────────────────────────────
  if (err.type === 'StripeCardError') {
    return fail(res, err.code || 'CARD_ERROR', err.message, 402);
  }

  if (err.type && err.type.startsWith('Stripe')) {
    return fail(res, 'PAYMENT_ERROR', err.message || 'Payment processing error', 402);
  }

  // ── Syntax error (malformed JSON body) ───────────────────────────────────
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return fail(res, 'INVALID_JSON', 'Invalid JSON in request body', 400);
  }

  // ── Generic 4xx forwarded as-is ───────────────────────────────────────────
  if (statusCode >= 400 && statusCode < 500) {
    return fail(res, 'REQUEST_ERROR', err.message || 'Bad Request', statusCode);
  }

  // ── Generic 500 ──────────────────────────────────────────────────────────
  // The stack trace is logged above and NEVER serialized into the response,
  // in any environment (AGENTS.md §3: never expose stack traces).
  return fail(
    res,
    'INTERNAL_ERROR',
    isProduction() ? 'Internal Server Error' : err.message,
    statusCode,
  );
};

export default errorHandler;
export { notFound };
