/**
 * betaGate — controlled launch gate (Waitlist/Beta).
 *
 * Guard an AI or checkout route so users are either:
 *  - 'active'      → pass
 *  - 'waitlist'    → 403 WAITLIST_PENDING (they can log in but not burn AI quota)
 *  - 'denied'      → 403 WAITLIST_DENIED
 *
 * When WAITLIST_MODE != true the middleware is a no-op (just calls next()),
 * so enabling the feature is server-side and env-driven only.
 */
import logger from '../utils/logger.js';

const WAITLIST_ENABLED = process.env.WAITLIST_MODE === 'true';

/**
 * Blocks AI-calling routes for users still on the waitlist.
 * Requires `protect` + `gateAI` to have already populated req.user.
 */
export function betaGate(req, res, next) {
  if (!WAITLIST_ENABLED) return next();
  if (!req.user) return next();

  const status = req.user.betaStatus || 'active';
  if (status === 'waitlist') {
    logger.info(`Waitlist user ${req.user.id} blocked from paid route`);
    return res.status(403).json({
      success: false,
      error: {
        code: 'WAITLIST_PENDING',
        message:
          'Your account is on the waitlist for launch. You will be able to generate once your spot is approved.',
      },
    });
  }
  if (status === 'denied') {
    return res.status(403).json({
      success: false,
      error: { code: 'WAITLIST_DENIED', message: 'This account is not authorized to generate.' },
    });
  }
  return next();
}

export default betaGate;
