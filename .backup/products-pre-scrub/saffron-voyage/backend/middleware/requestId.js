/**
 * Request-ID Correlation Middleware
 * ---------------------------------
 * Assigns a unique id per request (honours an incoming X-Request-Id when
 * present, otherwise generates a UUID). Stored on req.id and exposed back via
 * the X-Request-Id response header so distributed logs can be traced end-to-end.
 */
import { randomUUID } from 'crypto';

export const requestId = (req, res, next) => {
  const incoming = req.headers['x-request-id'];
  req.id = (incoming && String(incoming).trim()) || randomUUID();
  req.id = req.id.slice(0, 64);
  res.setHeader('X-Request-Id', req.id);
  next();
};

export default requestId;
