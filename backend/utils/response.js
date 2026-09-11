/**
 * Standardized JSON Response Wrapper
 * ----------------------------------
 * Contract:
 *   success true  → { success, data, meta? }
 *   success false → { success: false, error: { code, message }, details? }
 * All routes use sendSuccess / sendError instead of ad-hoc res.json shapes.
 */
const error = (res, code, message, status = 400, details = null, extra = {}) => {
  return res.status(status).json({
    success: false,
    error: { code, message, ...(details ? { details } : {}) },
    ...(Object.keys(extra).length ? { ...extra } : {}),
  });
};

const sendSuccess = (res, data = null, meta = undefined, status = 200) => {
  const body = { success: true, data };
  if (meta !== undefined) body.meta = meta;
  return res.status(status).json(body);
};

const sendError = (res, code, message, status = 400, details = null) => {
  return error(res, code, message, status, details);
};

const sendNotFound = (res, resource = 'Resource') => {
  return error(res, 'NOT_FOUND', `${resource} not found`, 404);
};

const sendValidationError = (res, details = null) => {
  return error(res, 'VALIDATION_ERROR', 'Validation failed', 422, details);
};

const sendUnauthorized = (res, message = 'Unauthorized') => {
  return error(res, 'UNAUTHORIZED', message, 401);
};

const sendForbidden = (res, message = 'Forbidden') => {
  return error(res, 'FORBIDDEN', message, 403);
};

const sendServerError = (res, message = 'Internal Server Error', details = null) => {
  return error(res, 'INTERNAL_ERROR', message, 500, details);
};

export default {
  sendSuccess,
  sendError,
  sendNotFound,
  sendValidationError,
  sendUnauthorized,
  sendForbidden,
  sendServerError,
};