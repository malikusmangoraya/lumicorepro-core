/**
 * Audit Logger — request audit trail, opt-in and fail-open.
 * Enable with AUDIT_LOG=true (default) or configure AUDIT_LOG_FILE.
 */
const fs = require('fs');
const path = require('path');

const enabled = process.env.AUDIT_LOG !== 'false';
const logFile = path.resolve(process.env.AUDIT_LOG_FILE || './audit.log');

const persist = (entry) => {
  try {
    fs.appendFileSync(logFile, entry + '\n');
    if (process.env.AUDIT_LOG_STDOUT !== 'false') {
      console.log(`[AUDIT] ${entry}`);
    }
  } catch (_) {
    /* noop */
  }
};

const auditRequest = (req, res, next) => {
  if (!enabled) return next();
  const startedAt = Date.now();
  res.once('finish', () => {
    try {
      persist(
        JSON.stringify({
          ts: new Date().toISOString(),
          method: req.method,
          url: req.originalUrl,
          status: res.statusCode,
          durationMs: Date.now() - startedAt,
          user: (req.user && (req.user.id || req.user.sub || req.user.email)) || null,
          ip: req.ip || (req.socket && req.socket.remoteAddress) || null,
          ua: req.headers['user-agent'] || null,
        })
      );
    } catch (_) {
      /* noop */
    }
  });
  next();
};

module.exports = { auditRequest, persist };
