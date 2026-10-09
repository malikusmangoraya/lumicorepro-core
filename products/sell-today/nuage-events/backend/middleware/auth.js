import jwt from 'jsonwebtoken';
// `utils/jwtSecret.js` is CommonJS. A default import always resolves for an
// interop module, unlike named imports which depend on static analysis.
import jwtSecretModule from '../utils/jwtSecret.js';

/**
 * Authentication and authorisation middleware.
 *
 * Exports:
 *   protect                     verify the bearer token, hydrate `req.user`
 *   optionalProtect             attach `req.user` when a token is present, never reject
 *   authorize(...roles)         require one of the listed roles
 *   adminOnly                   shorthand for authorize('admin')
 *   generateToken(user)         sign a short-lived access token
 *   registerInMemoryStore(map)  register the offline fallback user store
 */

const { jwtSecret } = jwtSecretModule;

const TOKEN_TTL = process.env.JWT_EXPIRES_IN || '15m';
const ALGORITHM = 'HS256';

/**
 * When no database is reachable the auth routes fall back to an in-memory Map
 * keyed by lower-cased email address. The routes register it here so `protect`
 * can hydrate a full user record from a token that only carries an id.
 */
let memoryStore = null;

/**
 * Register the fallback user store.
 * @param {Map<string, object>} store keyed by lower-cased email address
 */
export function registerInMemoryStore(store) {
  if (!(store instanceof Map)) {
    throw new TypeError('registerInMemoryStore expects a Map of users');
  }
  memoryStore = store;
  return store;
}

/** True when a fallback store has been registered and holds this user. */
function lookupMemoryUser(id) {
  if (!memoryStore || id === undefined || id === null) return null;
  for (const user of memoryStore.values()) {
    if (String(user.id) === String(id)) return user;
  }
  return null;
}

/**
 * Sign an access token.
 *
 * Accepts either a user id or a user object; when given an object the role is
 * carried in the payload so `authorize` can make a decision without a database
 * round trip on every request.
 *
 * @param {number|string|{id:*, role?:string}} user
 * @param {object} [extra] additional claims
 */
export function generateToken(user, extra = {}) {
  const isObject = user !== null && typeof user === 'object';
  const id = isObject ? user.id : user;
  const role = isObject ? user.role : undefined;
  const payload = { id, ...(role ? { role } : {}), ...extra };
  return jwt.sign(payload, jwtSecret, { expiresIn: TOKEN_TTL, algorithm: ALGORITHM });
}

function readBearerToken(req) {
  const header = req.headers?.authorization || '';
  if (!header.startsWith('Bearer ')) return null;
  const token = header.slice(7).trim();
  return token || null;
}

/**
 * Verify the access token on the request.
 *
 * On success `req.user` holds the token payload, enriched with the full record
 * when the in-memory fallback store knows the id.
 */
export async function protect(req, res, next) {
  const token = readBearerToken(req);
  if (!token) {
    return res.status(401).json({
      success: false,
      message: 'Not authorized, no token provided',
    });
  }

  let decoded;
  try {
    decoded = jwt.verify(token, jwtSecret, { algorithms: [ALGORITHM] });
  } catch (err) {
    const message = err.name === 'TokenExpiredError'
      ? 'Not authorized, token expired'
      : 'Not authorized, token failed';
    return res.status(401).json({ success: false, message });
  }

  const full = lookupMemoryUser(decoded.id);
  req.user = full ? { ...decoded, ...full, password: undefined } : decoded;
  return next();
}

/**
 * Restrict a route to the given roles.
 *
 * Must be used after `protect`, which is what populates `req.user`.
 *
 * @param {...string} roles
 */
export function authorize(...roles) {
  const allowed = roles.flat().filter(Boolean);
  return function authorizeMiddleware(req, res, next) {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Not authorized, no token provided',
      });
    }
    if (allowed.length === 0) return next();
    if (!allowed.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        message: 'Forbidden: insufficient permissions',
      });
    }
    return next();
  };
}

/** Shorthand for `authorize('admin')`. */
export const adminOnly = authorize('admin');

/**
 * Attach the caller when a valid token is present, but never reject.
 *
 * Used by endpoints that render a different experience for signed-in users
 * (a dashboard link in the nav, for example) and must stay reachable by
 * anonymous visitors. An invalid or absent token simply leaves `req.user`
 * undefined and the request continues.
 */
export async function optionalProtect(req, res, next) {
  const token = readBearerToken(req);
  if (!token) return next();
  try {
    const decoded = jwt.verify(token, jwtSecret, { algorithms: [ALGORITHM] });
    const full = lookupMemoryUser(decoded.id);
    req.user = full ? { ...decoded, ...full, password: undefined } : decoded;
  } catch {
    // An unusable token is treated as no token at all.
  }
  return next();
}

export default {
  protect,
  optionalProtect,
  authorize,
  adminOnly,
  generateToken,
  registerInMemoryStore,
};
