/**
 * Application Error (HTTP-aware)
 * ------------------------------
 * Carries the HTTP status + machine-readable code through `next(err)` so the
 * global error handler can serialize the canonical error envelope from the
 * error itself instead of guessing from `res.statusCode`.
 *
 *   throw new AppError('Order not found', 404, 'ORDER_NOT_FOUND');
 */

/** Default machine-readable codes per HTTP status (used when no code is given). */
const DEFAULT_CODES = {
  400: 'BAD_REQUEST',
  401: 'UNAUTHORIZED',
  403: 'FORBIDDEN',
  404: 'NOT_FOUND',
  409: 'CONFLICT',
  413: 'PAYLOAD_TOO_LARGE',
  422: 'VALIDATION_ERROR',
  429: 'RATE_LIMITED',
  500: 'INTERNAL_ERROR',
  502: 'BAD_GATEWAY',
  503: 'SERVICE_UNAVAILABLE',
};

class AppError extends Error {
  /**
   * @param {string} message - Safe, user-facing message (never a stack trace)
   * @param {number} [statusCode=500] - HTTP status to respond with
   * @param {string|null} [code=null] - Machine-readable code (status-derived default)
   * @param {object|Array|null} [details=null] - Optional field-level details
   */
  constructor(message, statusCode = 500, code = null, details = null) {
    super(message || DEFAULT_CODES[statusCode] || 'Unexpected error');
    this.name = 'AppError';
    this.statusCode = statusCode;
    this.status = statusCode; // Express reads err.status/err.statusCode for 4xx passthrough
    this.code = code || DEFAULT_CODES[statusCode] || 'ERROR';
    this.details = details;
    this.isAppError = true;
    if (typeof Error.captureStackTrace === 'function') Error.captureStackTrace(this, AppError);
  }
}

/** Duck-typed check so a cross-realm/duplicated copy still counts as an AppError. */
export const isAppError = (err) => err instanceof AppError || err?.isAppError === true;

export { AppError };
export default AppError;
