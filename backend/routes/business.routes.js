/**
 * LumicorePro — Business Routes
 * Provides business-level analytics, configurable reports, and tenant settings.
 * Intended for vendor/admin users managing their own business metrics.
 */
import express from 'express';
import { Op, fn, col } from 'sequelize';
import { body, validationResult } from 'express-validator';
import Order from '../models/Order.js';
import User from '../models/User.js';
import Product from '../models/Product.js';
import Payment from '../models/Payment.js';
import { protect, authorize } from '../middleware/auth.js';
import { callerOrgId, tenantWhere } from '../services/tenantScope.service.js';
import logger from '../utils/logger.js';

const router = express.Router();

router.use(protect);

const PERIOD_DAYS = { week: 7, month: 30, quarter: 90, year: 365 };
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/** `YYYY-MM-DD` → UTC midnight; full ISO instants are accepted too. Null when invalid. */
const parseDateParam = (value) => {
  if (typeof value !== 'string' || value.trim() === '') return null;
  if (ISO_DATE.test(value)) {
    const date = new Date(`${value}T00:00:00.000Z`);
    if (Number.isNaN(date.getTime())) return null;
    // `new Date('2026-02-30')` silently rolls over to March; a round trip
    // proves the calendar date the caller sent exists.
    return date.toISOString().slice(0, 10) === value ? date : null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

/**
 * `users` has no immutable org membership column — `current_org_id` is the
 * caller's active org and the closest available scope. Counting without it
 * merged every tenant's signups into one number.
 */
const userTenantWhere = (req) => {
  const orgId = callerOrgId(req);
  return orgId === null ? { current_org_id: { [Op.is]: null } } : { current_org_id: orgId };
};

/**
 * GET /api/business/analytics
 * Comprehensive business metrics with optional date range filtering.
 * Query params: period=week|month|quarter|year  or  startDate / endDate
 */
router.get('/analytics', authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const { period: rawPeriod = 'month', startDate: sdParam, endDate: edParam } = req.query;

    if (!Object.hasOwn(PERIOD_DAYS, rawPeriod)) {
      return res.status(400).json({
        success: false,
        error: 'period must be one of week, month, quarter, year',
      });
    }
    const period = rawPeriod;

    let start, end;
    if (sdParam) {
      start = parseDateParam(sdParam);
      if (!start) {
        return res.status(400).json({ success: false, error: 'startDate must be a real YYYY-MM-DD date' });
      }
      end = edParam ? parseDateParam(edParam) : new Date();
      if (!end) {
        return res.status(400).json({ success: false, error: 'endDate must be a real YYYY-MM-DD date' });
      }
      if (start.getTime() > end.getTime()) {
        return res.status(400).json({ success: false, error: 'startDate must not be after endDate' });
      }
    } else {
      end   = new Date();
      start = new Date();
      start.setDate(start.getDate() - PERIOD_DAYS[period]);
    }

    const prevStart = new Date(start);
    prevStart.setDate(prevStart.getDate() - PERIOD_DAYS[period]);

    // Every aggregate is pinned to the caller's tenant. Without this a vendor
    // asking for "their" revenue received a SUM over every organization.
    const tenant = tenantWhere(req);
    const userTenant = userTenantWhere(req);
    const dateWhere      = { ...tenant, createdAt: { [Op.between]: [start, end] } };
    const prevDateWhere  = { ...tenant, createdAt: { [Op.between]: [prevStart, start] } };

    const [
      currRevRow, prevRevRow,
      currOrders, prevOrders,
      currUsers,  prevUsers,
      ordersByStatus,
      paymentMethods,
    ] = await Promise.all([
      // Current period revenue
      Order.findOne({
        attributes: [[fn('SUM', col('totalPrice')), 'revenue']],
        where: { isPaid: true, ...dateWhere },
        raw: true,
      }),
      // Previous period revenue (for % change)
      Order.findOne({
        attributes: [[fn('SUM', col('totalPrice')), 'revenue']],
        where: { isPaid: true, ...prevDateWhere },
        raw: true,
      }),
      // Orders this period
      Order.count({ where: dateWhere }),
      Order.count({ where: prevDateWhere }),
      // Users this period
      User.count({ where: { ...userTenant, createdAt: { [Op.between]: [start, end] } } }),
      User.count({ where: { ...userTenant, createdAt: { [Op.between]: [prevStart, start] } } }),
      // Orders by status
      Order.findAll({
        attributes: ['status', [fn('COUNT', col('id')), 'count']],
        where: dateWhere,
        group: ['status'],
        raw: true,
      }),
      // Revenue by payment method
      Payment.findAll({
        attributes: ['provider', [fn('SUM', col('amount')), 'total'], [fn('COUNT', col('id')), 'count']],
        where: { ...tenant, status: 'succeeded', ...dateWhere },
        group: ['provider'],
        raw: true,
      }),
    ]);

    const currRev = parseFloat(currRevRow?.revenue || 0);
    const prevRev = parseFloat(prevRevRow?.revenue || 0);
    const revChange = prevRev > 0 ? Math.round(((currRev - prevRev) / prevRev) * 100) : null;

    const ordChange = prevOrders > 0 ? Math.round(((currOrders - prevOrders) / prevOrders) * 100) : null;
    const usrChange = prevUsers  > 0 ? Math.round(((currUsers  - prevUsers)  / prevUsers)  * 100) : null;

    res.json({
      success: true,
      period,
      startDate: start,
      endDate:   end,
      data: {
        revenue: {
          current:    Math.round(currRev  * 100) / 100,
          previous:   Math.round(prevRev  * 100) / 100,
          changePercent: revChange,
        },
        orders: {
          current:  currOrders,
          previous: prevOrders,
          changePercent: ordChange,
          byStatus: ordersByStatus.map((s) => ({ status: s.status, count: parseInt(s.count, 10) })),
        },
        users: {
          current:  currUsers,
          previous: prevUsers,
          changePercent: usrChange,
        },
        paymentMethods: paymentMethods.map((p) => ({
          provider: p.provider,
          total:    Math.round(parseFloat(p.total || 0) * 100) / 100,
          count:    parseInt(p.count, 10),
        })),
      },
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/business/reports
 * Downloadable / displayable business summary report.
 */
router.get('/reports', authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const { format = 'json', period: rawPeriod = 'month' } = req.query;

    // Reflecting an unvalidated `period` put caller text into the CSV body and
    // the Content-Disposition filename.
    if (!Object.hasOwn(PERIOD_DAYS, rawPeriod)) {
      return res.status(400).json({
        success: false,
        error: 'period must be one of week, month, quarter, year',
      });
    }
    const period = rawPeriod;
    const days = PERIOD_DAYS[period];
    const since = new Date();
    since.setDate(since.getDate() - days);

    const tenant = tenantWhere(req);
    const userTenant = userTenantWhere(req);

    const [
      totalRevRow, orderCount, newUsers, productCount,
      topProductRows, statusRows,
    ] = await Promise.all([
      Order.findOne({
        attributes: [
          [fn('SUM', col('totalPrice')), 'revenue'],
          [fn('AVG', col('totalPrice')), 'avgOrder'],
        ],
        where: { ...tenant, isPaid: true, createdAt: { [Op.gte]: since } },
        raw: true,
      }),
      Order.count({ where: { ...tenant, createdAt: { [Op.gte]: since } } }),
      User.count({ where: { ...userTenant, createdAt: { [Op.gte]: since } } }),
      Product.count({ where: { ...tenant, isActive: true } }),
      // Top product categories
      Product.findAll({
        attributes: ['category', [fn('COUNT', col('id')), 'count']],
        where: { ...tenant, isActive: true },
        group: ['category'],
        order: [[fn('COUNT', col('id')), 'DESC']],
        limit: 5,
        raw: true,
      }),
      // Order status breakdown
      Order.findAll({
        attributes: ['status', [fn('COUNT', col('id')), 'count']],
        where: { ...tenant, createdAt: { [Op.gte]: since } },
        group: ['status'],
        raw: true,
      }),
    ]);

    const report = {
      generatedAt:  new Date().toISOString(),
      period,
      summary: {
        revenue:      Math.round(parseFloat(totalRevRow?.revenue  || 0) * 100) / 100,
        avgOrder:     Math.round(parseFloat(totalRevRow?.avgOrder || 0) * 100) / 100,
        orders:       orderCount,
        newUsers,
        activeProducts: productCount,
      },
      ordersByStatus:   statusRows.map((s) => ({ status: s.status, count: parseInt(s.count, 10) })),
      topCategories:    topProductRows.map((c) => ({ category: c.category, products: parseInt(c.count, 10) })),
    };

    if (format === 'csv') {
      const lines = [
        'Metric,Value',
        `Report Period,${period}`,
        `Generated At,${report.generatedAt}`,
        `Total Revenue,$${report.summary.revenue}`,
        `Average Order,$${report.summary.avgOrder}`,
        `Total Orders,${report.summary.orders}`,
        `New Users,${report.summary.newUsers}`,
        `Active Products,${report.summary.activeProducts}`,
      ];
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename="report-${period}.csv"`);
      return res.send(lines.join('\n'));
    }

    res.json({ success: true, data: report });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/business/settings
 * Retrieve current business/tenant settings stored in the vendor's user record.
 */
router.get('/settings', authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const user = await User.findByPk(req.user.id, {
      attributes: ['id', 'name', 'email', 'phone', 'avatar', 'preferences'],
    });

    if (!user) return res.status(404).json({ success: false, error: 'User not found' });

    const prefs = user.preferences || {};
    const settings = {
      businessName:    prefs.businessName    || user.name,
      email:           user.email,
      phone:           user.phone || '',
      avatar:          user.avatar || '',
      currency:        prefs.currency        || 'USD',
      timezone:        prefs.timezone        || 'UTC',
      language:        prefs.language        || 'en',
      theme:           prefs.theme           || 'dark',
      notifications:   prefs.notifications   || { email: true, push: true },
      taxRate:         prefs.taxRate         || 8,
      freeShippingMin: prefs.freeShippingMin || 100,
      shippingRate:    prefs.shippingRate    || 9.99,
    };

    res.json({ success: true, data: settings });
  } catch (error) {
    next(error);
  }
});

/**
 * PUT /api/business/settings
 * Update business settings (stored in user preferences JSONB).
 */
router.put(
  '/settings',
  authorize('admin', 'vendor'),
  [
    body('businessName').optional().trim().notEmpty().withMessage('Business name cannot be empty'),
    body('currency').optional().isLength({ min: 3, max: 3 }).withMessage('Currency must be a 3-letter code'),
    body('taxRate').optional().isFloat({ min: 0, max: 100 }).withMessage('Tax rate must be 0–100'),
    body('shippingRate').optional().isFloat({ min: 0 }).withMessage('Shipping rate must be non-negative'),
  ],
  async (req, res, next) => {
    try {
      const errs = validationResult(req);
      if (!errs.isEmpty()) {
        return res.status(400).json({ success: false, errors: errs.array() });
      }

      const user = await User.findByPk(req.user.id);
      if (!user) return res.status(404).json({ success: false, error: 'User not found' });

      const {
        businessName, currency, timezone, language, theme,
        notifications, taxRate, freeShippingMin, shippingRate,
        phone, avatar,
      } = req.body;

      const currentPrefs = user.preferences || {};
      const updatedPrefs = {
        ...currentPrefs,
        ...(businessName    !== undefined && { businessName }),
        ...(currency        !== undefined && { currency }),
        ...(timezone        !== undefined && { timezone }),
        ...(language        !== undefined && { language }),
        ...(theme           !== undefined && { theme }),
        ...(taxRate         !== undefined && { taxRate: parseFloat(taxRate) }),
        ...(freeShippingMin !== undefined && { freeShippingMin: parseFloat(freeShippingMin) }),
        ...(shippingRate    !== undefined && { shippingRate: parseFloat(shippingRate) }),
        ...(notifications   !== undefined && {
          notifications: { ...currentPrefs.notifications, ...notifications },
        }),
      };

      const userUpdates = { preferences: updatedPrefs };
      if (phone  !== undefined) userUpdates.phone  = phone;
      if (avatar !== undefined) userUpdates.avatar = avatar;

      await user.update(userUpdates);

      logger.info(`Business settings updated for user ${req.user.id}`);

      res.json({ success: true, message: 'Settings updated successfully', data: updatedPrefs });
    } catch (error) {
      next(error);
    }
  }
);

export default router;
