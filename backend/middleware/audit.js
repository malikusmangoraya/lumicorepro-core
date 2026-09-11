import AuditLog from '../models/AuditLog.js';

function clientIp(req) {
  return (
    req?.headers?.['x-forwarded-for']?.split(',')[0]?.trim() ||
    req?.socket?.remoteAddress ||
    ''
  );
}

/**
 * Persist an audit entry. Fire-and-forget: never blocks the request or
 * throws — failure to record must not break the primary action.
 */
export async function recordAudit(req, { action, userId = null, email = null, meta = null }) {
  try {
    await AuditLog.create({
      user_id: userId,
      email,
      action,
      ip: clientIp(req).slice(0, 45),
      user_agent: (req?.headers?.['user-agent'] || '').slice(0, 255),
      meta,
    });
  } catch {
    /* audit trail must never affect the primary request */
  }
}

/**
 * Express middleware — records the action on response finish.
 * Usage: router.post('/x', auditTrail('auth.login.failure'), handler)
 */
export function auditTrail(action) {
  return (req, res, next) => {
    res.on('finish', () => {
      recordAudit(req, { action, userId: req.user?.id ?? null, email: req.user?.email ?? null });
    });
    next();
  };
}