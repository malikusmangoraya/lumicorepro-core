/**
 * Apex — Audit Log Routes (Admin)
 * ---------------------------------------------------------------
 * Read-only enterprise audit trail. Every user action recorded by the
 * `recordAudit` middleware is queryable + exportable to CSV.
 *
 * GET  /api/audit-logs                 — paginated, filterable
 * GET  /api/audit-logs/export          — full CSV export (filterable)
 */
import express from 'express';
import { Op } from 'sequelize';
import AuditLog from '../models/AuditLog.js';
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
        [
          r.id,
          r.created_at?.toISOString() || '',
          r.user_id,
          r.email,
          r.action,
          r.ip,
          r.user_agent,
          JSON.stringify(r.meta || {}),
        ]
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

export default router;
