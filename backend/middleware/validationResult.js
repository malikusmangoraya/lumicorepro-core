/**
 * Terminal middleware for express-validator chains.
 *
 * `validateRequest` is the Zod counterpart and is a FACTORY
 * (`validateRequest(schema) => middleware`); routes that declare
 * `body()/query()/param()` chains need this instead. Mounting the bare Zod
 * factory in a chain returned a function without calling `next()`, which
 * stalled the request until the client timed out.
 */
import { validationResult } from 'express-validator';
import resp from '../utils/response.js';

export const checkValidation = (req, res, next) => {
  const errors = validationResult(req);
  if (errors.isEmpty()) return next();

  const details = errors.array().map((e) => ({
    path: e.path || '(root)',
    message: e.msg,
  }));
  return resp.sendValidationError(res, details);
};

export default checkValidation;
