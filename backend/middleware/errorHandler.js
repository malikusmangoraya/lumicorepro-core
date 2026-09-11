import logger from '../utils/logger.js';
import resp from '../utils/response.js';

// ── 404 handler ─────────────────────────────────────────────────────────────
const notFound = (req, res, next) => {
  res.status(404);
  res.json(resp.sendNotFound(res, `Route ${req.method} ${req.originalUrl}`));
};

// ── Global error handler ─────────────────────────────────────────────────────
const errorHandler = (err, req, res, next) => {
  const statusCode = res.statusCode === 200 ? 500 : res.statusCode;

  // Log error details
  logger.error(`[${req.method}] ${req.originalUrl} — ${err.message}`, {
    stack: err.stack,
    ip: req.ip,
  });

  // ── Sequelize: Unique constraint (e.g. duplicate email) ──────────────────
  if (err.name === 'SequelizeUniqueConstraintError') {
    const fields = err.errors?.map((e) => e.path).join(', ') || 'field';
    return res.status(400).json({
      success: false,
      error: `Duplicate value: ${fields} already exists`,
    });
  }

  // ── Sequelize: Validation error (model-level validators) ─────────────────
  if (err.name === 'SequelizeValidationError') {
    const errors = err.errors?.map((e) => e.message) || [err.message];
    return res.status(400).json({
      success: false,
      error: 'Validation Error',
      details: errors,
    });
  }

  // ── Sequelize: Database connection error ──────────────────────────────────
  if (err.name === 'SequelizeConnectionError' || err.name === 'SequelizeConnectionRefusedError') {
    return res.status(503).json({
      success: false,
      error: 'Database connection unavailable. Please try again shortly.',
    });
  }

  // ── Sequelize: Generic database error ────────────────────────────────────
  if (err.name?.startsWith('Sequelize')) {
    return res.status(500).json({
      success: false,
      error: process.env.NODE_ENV === 'production'
        ? 'A database error occurred'
        : err.message,
    });
  }

  // ── JWT errors ────────────────────────────────────────────────────────────
  if (err.name === 'JsonWebTokenError') {
    return res.status(401).json({
      success: false,
      error: 'Invalid token',
    });
  }

  if (err.name === 'TokenExpiredError') {
    return res.status(401).json({
      success: false,
      error: 'Token expired — please log in again',
    });
  }

  // ── Multer / file upload errors ───────────────────────────────────────────
  if (err.code === 'LIMIT_FILE_SIZE') {
    return res.status(413).json({
      success: false,
      error: 'File too large. Maximum allowed size is 10 MB.',
    });
  }

  if (err.code === 'LIMIT_UNEXPECTED_FILE') {
    return res.status(400).json({
      success: false,
      error: 'Unexpected file field in upload request.',
    });
  }

  // ── Stripe payment errors ─────────────────────────────────────────────────
  if (err.type === 'StripeCardError') {
    return res.status(402).json({
      success: false,
      error: err.message,
      code: err.code,
    });
  }

  if (err.type && err.type.startsWith('Stripe')) {
    return res.status(402).json({
      success: false,
      error: err.message || 'Payment processing error',
    });
  }

  // ── Syntax error (malformed JSON body) ───────────────────────────────────
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({
      success: false,
      error: 'Invalid JSON in request body',
    });
  }

  // ── Generic 4xx forwarded as-is ───────────────────────────────────────────
  if (statusCode >= 400 && statusCode < 500) {
    return res.status(statusCode).json({
      success: false,
      error: err.message || 'Bad Request',
    });
  }

  // ── Generic 500 ───────────────────────────────────────────────────────────
  return res.status(statusCode).json({
    success: false,
    error: process.env.NODE_ENV === 'production' ? 'Internal Server Error' : err.message,
    ...(process.env.NODE_ENV !== 'production' && { stack: err.stack }),
  });
};

export default errorHandler;
export { notFound };
