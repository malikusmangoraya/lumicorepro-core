/**
 * Reusable Validation Middleware (Zod)
 * -------------------------------------
 * validateRequest(schema) validates req.body / req.query / req.params against
 * a zod schema centrally — routes pass a schema, no per-route validation code.
 * On failure returns 422 with standardized error shape.
 *
 * A schema is `{ body, query, params }`; whichever part is absent is skipped.
 * Parsing REPLACES the part, so unknown client keys are stripped before the
 * handler reads them — that is the point of this middleware, not a side effect.
 */
import { ZodError } from 'zod';
import resp from '../utils/response.js';

/**
 * `{ body, query, params }` live on `schema.shape` for a Zod object and on the
 * instance itself for a plain object literal. Reading only the instance — the
 * original behaviour — made every `validateRequest(zodSchema)` route destructure
 * three `undefined`s and pass the request through looking validated while it was
 * not validated at all. Supporting both keeps that trap from coming back.
 */
const partsOf = (schema) => (schema && (schema.shape || schema)) || {};

export const validateRequest = (schema) => (req, res, next) => {
  const { body, query, params } = partsOf(schema);
  try {
    if (body) req.body = body.parse(req.body);
    if (query) req.query = query.parse(req.query);
    if (params) req.params = params.parse(req.params);
    next();
  } catch (err) {
    if (err instanceof ZodError) {
      const details = err.issues.map((i) => ({
        path: i.path.join('.') || '(root)',
        message: i.message,
      }));
      return resp.sendValidationError(res, details);
    }
    return resp.sendServerError(res, 'Validation middleware error');
  }
};

export default validateRequest;
