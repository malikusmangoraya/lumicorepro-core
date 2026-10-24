/**
 * LumicorePro — Audit Log Routes (Admin)
 * ---------------------------------------------------------------
 * Read-only enterprise audit trail. Every user action recorded by the
 * `recordAudit` middleware is queryable + exportable to CSV.
 *
 * GET  /api/audit-logs                 — paginated, filterable
 * GET  /api/audit-logs/export          — full CSV export (filterable)
 */
import express from 'express';
import { Op } from 'sequelize';
import AuditLog, { purgeAuditLogs, verifyAuditChain } from '../models/AuditLog.js';
import { protect, authorize } from '../middleware/auth.js';

const router = express.Router();

router.use(protect, authorize('admin'));

const badQuery = (message) => Object.assign(new Error(message), { statusCode: 400 });

/** Build a Sequelize where-clause from admin query filters. */
function buildWhere(query) {
  const where = {};
  if (query.action) where.action = { [Op.iLike]: `%${query.action}%` };
  if (query.userId !== undefined && query.userId !== '') {
    const userId = Number(query.userId);
    if (!Number.isInteger(userId) || userId < 1) throw badQuery('userId must be a positive integer');
    where.user_id = userId;
  }
  if (query.email) where.email = { [Op.iLike]: `%${query.email}%` };
  if (query.ip) where.ip = query.ip;
  if (query.from || query.to) {
    where.created_at = {};
    for (const [param, operator] of [['from', Op.gte], ['to', Op.lte]]) {
      if (!query[param]) continue;
      const date = new Date(query[param]);
      // An Invalid Date serialises to null and the query then fails inside
      // PostgreSQL with a 500 instead of naming the bad parameter.
      if (Number.isNaN(date.getTime())) throw badQuery(`${param} must be a valid date`);
      where.created_at[operator] = date;
    }
  }
  return where;
}

function csvEscape(value) {
  const str = value === null || value === undefined ? '' : String(value);
  return `"${str.replace(/"/g, '""')}"`;
}

/**
 * @swagger
 * /api/audit/verify:
 *   get:
 *     summary: Recompute the audit hash chain and report tampering (admin)
 *     tags: [Audit]
 *     security: [{ bearerAuth: [] }]
 */
router.get('/verify', async (req, res, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 5000, 50000);
    const result = await verifyAuditChain(AuditLog, limit);
    // A broken chain is a security incident: log it server-side too.
    if (!result.valid) {
      const { logger } = await import('../utils/logger.js');
      logger.error(`AUDIT CHAIN BROKEN at id=${result.brokenAtId}: ${result.reason}`);
    }
    return res.json({ success: result.valid, ...result });
  } catch (err) {
    next(err);
  }
});

/**
 * @swagger
 * /api/audit-logs:
 *   get:
 *     summary: List audit events (admin) with action/user/date filters
 *     tags: [Audit]
 *     security: [{ bearerAuth: [] }]
 */
router.get('/', async (req, res, next) => {
  try {
    const rawPage = parseInt(req.query.page, 10);
    const rawLimit = parseInt(req.query.limit, 10);
    const page = rawPage > 0 ? rawPage : 1;
    const limit = rawLimit > 0 ? Math.min(rawLimit, 100) : 20;
    const offset = (page - 1) * limit;
    const where = buildWhere(req.query);

    const { count, rows } = await AuditLog.findAndCountAll({
      where,
      order: [['created_at', 'DESC']],
      limit,
      offset,
    });

    res.json({
      success: true,
      total: count,
      pagination: { page, limit, pages: Math.ceil(count / limit) },
      data: rows,
    });
  } catch (error) {
    if (error.statusCode) return res.status(error.statusCode).json({ success: false, error: error.message });
    next(error);
  }
});

/**
 * @swagger
 * /api/audit-logs/export:
 *   get:
 *     summary: Export audit events to CSV (admin)
 *     tags: [Audit]
 *     security: [{ bearerAuth: [] }]
 */
router.get('/export', async (req, res, next) => {
  try {
    const rawLimit = parseInt(req.query.limit, 10);
    const limit = rawLimit > 0 ? Math.min(rawLimit, 50000) : 10000;
    const where = buildWhere(req.query);
    const rows = await AuditLog.findAll({ where, order: [['created_at', 'DESC']], limit });

    const header = ['id', 'created_at', 'user_id', 'email', 'action', 'ip', 'user_agent', 'meta'];
    const lines = [
      header.join(','),
      ...rows.map((r) =>
        [r.id, r.created_at?.toISOString() || '', r.user_id, r.email, r.action, r.ip, r.user_agent, JSON.stringify(r.meta || {})]
          .map(csvEscape)
          .join(',')
      ),
    ];

    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', 'attachment; filename="audit-logs.csv"');
    return res.send(`\uFEFF${lines.join('\n')}`);
  } catch (error) {
    if (error.statusCode) return res.status(error.statusCode).json({ success: false, error: error.message });
    next(error);
  }
});

/**
 * @swagger
 * /api/audit-logs/retention:
 *   delete:
 *     summary: Purge audit rows older than a cutoff (admin, explicit confirm)
 *     tags: [Audit]
 *     security: [{ bearerAuth: [] }]
 */
router.delete('/retention', async (req, res, next) => {
  try {
    const { before, confirm } = req.body || {};
    const cutoff = new Date(before || '');
    if (Number.isNaN(cutoff.getTime())) {
      return res.status(400).json({ success: false, error: 'before (ISO date) is required' });
    }
    if (confirm !== 'PURGE-AUDIT-LOGS') {
      return res.status(400).json({
        success: false,
        error: 'Retention purge requires explicit confirmation (confirm: "PURGE-AUDIT-LOGS")',
      });
    }
    const deleted = await purgeAuditLogs(cutoff);
    return res.json({ success: true, data: { deleted, before: cutoff.toISOString() } });
  } catch (error) {
    next(error);
  }
});

export default router;