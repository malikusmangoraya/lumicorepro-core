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

/** Build a Sequelize where-clause from admin query filters. */
function buildWhere(query) {
  const where = {};
  if (query.action) where.action = { [Op.iLike]: `%${query.action}%` };
  if (query.userId) where.user_id = parseInt(query.userId, 10);
  if (query.email) where.email = { [Op.iLike]: `%${query.email}%` };
  if (query.ip) where.ip = query.ip;
  if (query.from || query.to) {
    where.created_at = {};
    if (query.from) where.created_at[Op.gte] = new Date(query.from);
    if (query.to) where.created_at[Op.lte] = new Date(query.to);
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
    const page = parseInt(req.query.page, 10) || 1;
    const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
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
    const limit = Math.min(parseInt(req.query.limit, 10) || 10000, 50000);
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