/**
 * Reusable Validation Middleware (Zod)
 * -------------------------------------
 * validateRequest(schema) validates req.body / req.query / req.params against
 * a zod schema centrally — routes pass a schema, no per-route validation code.
 * On failure returns 422 with standardized error shape.
 */
import { ZodError } from 'zod';
import resp from '../utils/response.js';

const defaultSchema = { body: undefined, query: undefined, params: undefined };

export const validateRequest =
  ({ body, query, params } = defaultSchema) =>
  (req, res, next) => {
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
