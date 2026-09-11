import jwt from 'jsonwebtoken';
import User from '../models/User.js';
import logger from '../utils/logger.js';

/**
 * In-memory fallback store (mirrors the one in auth.routes.js).
 * Allows users registered via the offline fallback to pass protect() checks
 * even when the Postgres DB is unavailable.
 * NOTE: This Map is populated by auth.routes.js at startup — imported here as
 * a shared module-level singleton via the re-exported getter.
 */
let _inMemoryStore = null;

/**
 * Called by auth.routes.js to register its in-memory store with this middleware
 * so protect() can fall back to it when Postgres is unreachable.
 */
export function registerInMemoryStore(store) {
  _inMemoryStore = store;
}

export const protect = async (req, res, next) => {
  let token;

  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    try {
      token = req.headers.authorization.split(' ')[1];

      // Verify JWT signature
      const decoded = jwt.verify(token, process.env.JWT_SECRET);

      // 1. Try Postgres first
      let user = null;
      try {
        const dbUser = await User.findByPk(decoded.id, {
          attributes: { exclude: ['password'] },
        });
        if (dbUser) {
          user = dbUser.get({ plain: true });
        }
      } catch (dbErr) {
        logger.warn(`protect(): Postgres lookup failed (${dbErr.message}), checking in-memory store`);
      }

      // 2. Fallback to in-memory store (offline mode / demo users)
      if (!user && _inMemoryStore) {
        for (const memUser of _inMemoryStore.values()) {
          if (String(memUser.id) === String(decoded.id)) {
            // Strip password from in-memory user before attaching to req
            const { password: _pw, comparePassword: _cp, save: _sv, ...safeUser } = memUser;
            user = safeUser;
            break;
          }
        }
      }

      if (!user) {
        return res.status(401).json({
          success: false,
          error: 'User not found',
        });
      }

      if (user.isActive === false) {
        return res.status(401).json({
          success: false,
          error: 'User account is deactivated',
        });
      }

      req.user = user;
      next();
    } catch (error) {
      logger.error(`Auth middleware error: ${error.message}`);
      return res.status(401).json({
        success: false,
        error: 'Not authorized, token failed',
      });
    }
  } else {
    if (!token) {
      return res.status(401).json({
        success: false,
        error: 'Not authorized, no token',
      });
    }
  }
};

export const authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        error: `User role '${req.user?.role}' is not authorized to access this route`,
      });
    }
    next();
  };
};

// Generate JWT token — expects Sequelize integer primary key or in-memory numeric id
export const generateToken = (id) => {
  return jwt.sign({ id }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRE || '7d',
  });
};
