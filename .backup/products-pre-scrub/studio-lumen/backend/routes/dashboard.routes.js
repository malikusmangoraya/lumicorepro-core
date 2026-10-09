/**
 * LumicorePro — Dashboard Routes
 * Serves KPI stats, charts, reports, and activity feed for the admin dashboard.
 * All endpoints are Sequelize/PostgreSQL — no MongoDB dependencies.
 */
import express from 'express';
import { Op, fn, col, literal } from 'sequelize';
import Order from '../models/Order.js';
import User from '../models/User.js';
import Product from '../models/Product.js';
import Payment from '../models/Payment.js';
import Notification from '../models/Notification.js';
import AnalyticsEvent from '../models/AnalyticsEvent.js';
import { protect, authorize } from '../middleware/auth.js';
import cache from '../services/cache/cache.service.js';

const router = express.Router();

// All dashboard routes require auth
router.use(protect);

/**
 * GET /api/dashboard/stats
 * Core KPIs: revenue, orders, users, products, conversion rate, avg order value
 * Cached for 2 min (Redis or in-memory fallback); invalidated on order writes.
 */
router.get('/stats', authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const statsKey = `dashboard:stats`;
    const cached = await cache.get('dashboard', statsKey);
    if (cached) return res.json({ success: true, data: cached, meta: { cached: true } });

    const [totalUsers, totalProducts, totalOrders, lowStock, revenueRow, pendingOrders] =
      await Promise.all([
        User.count(),
        Product.count({ where: { isActive: true } }),
        Order.count(),
        Product.count({ where: { stock: { [Op.lte]: 5 }, isActive: true } }),
        Order.findOne({
          attributes: [
            [fn('SUM', col('totalPrice')), 'totalRevenue'],
            [fn('AVG', col('totalPrice')), 'avgOrderValue'],
          ],
          where: { isPaid: true },
          raw: true,
        }),
        Order.count({ where: { status: 'pending' } }),
      ]);

    const totalRevenue = parseFloat(revenueRow?.totalRevenue || 0);
    const avgOrderValue = parseFloat(revenueRow?.avgOrderValue || 0);

    const data = {
      totalRevenue: Math.round(totalRevenue * 100) / 100,
      totalOrders,
      totalUsers,
      totalProducts,
      lowStockProducts: lowStock,
      pendingOrders,
      avgOrderValue: Math.round(avgOrderValue * 100) / 100,
      conversionRate: totalUsers > 0 ? Math.round((totalOrders / totalUsers) * 100) / 100 : 0,
    };

    await cache.set('dashboard', statsKey, data, cache.TTL.DASHBOARD);
    return res.json({ success: true, data });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/dashboard/charts/:type
 * Dynamic chart data. type = revenue | orders | users | products
 */
router.get('/charts/:type', authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const { type } = req.params;
    const days = parseInt(req.query.days, 10) || 30;
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    let data;

    if (type === 'revenue' || type === 'orders') {
      const rows = await Order.findAll({
        attributes: [
          [fn('DATE', col('createdAt')), 'date'],
          [fn('SUM', col('totalPrice')), 'revenue'],
          [fn('COUNT', col('id')), 'orders'],
        ],
        where: { createdAt: { [Op.gte]: startDate } },
        group: [fn('DATE', col('createdAt'))],
        order: [[fn('DATE', col('createdAt')), 'ASC']],
        raw: true,
      });
      data = rows.map((r) => ({
        date: r.date,
        revenue: Math.round(parseFloat(r.revenue || 0) * 100) / 100,
        orders: parseInt(r.orders, 10),
      }));
    } else if (type === 'users') {
      const rows = await User.findAll({
        attributes: [
          [fn('DATE', col('createdAt')), 'date'],
          [fn('COUNT', col('id')), 'count'],
        ],
        where: { createdAt: { [Op.gte]: startDate } },
        group: [fn('DATE', col('createdAt'))],
        order: [[fn('DATE', col('createdAt')), 'ASC']],
        raw: true,
      });
      data = rows.map((r) => ({ date: r.date, count: parseInt(r.count, 10) }));
    } else if (type === 'products') {
      const rows = await Product.findAll({
        attributes: ['category', [fn('COUNT', col('id')), 'count']],
        where: { isActive: true },
        group: ['category'],
        order: [[fn('COUNT', col('id')), 'DESC']],
        raw: true,
      });
      data = rows.map((r) => ({ category: r.category, count: parseInt(r.count, 10) }));
    } else {
      return res.status(400).json({ success: false, error: `Unknown chart type: ${type}` });
    }

    res.json({ success: true, type, days, data });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/dashboard/activity
 * Recent platform activity: orders, registrations, reviews (last N items)
 */
router.get('/activity', authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 10, 50);

    const [recentOrders, recentUsers] = await Promise.all([
      Order.findAll({
        include: [
          {
            model: User,
            as: 'user',
            attributes: ['id', 'name', 'email', 'avatar'],
            required: false,
          },
        ],
        order: [['createdAt', 'DESC']],
        limit,
      }),
      User.findAll({
        attributes: { exclude: ['password'] },
        order: [['createdAt', 'DESC']],
        limit: Math.ceil(limit / 2),
      }),
    ]);

    // Merge and sort by createdAt into a unified activity feed
    const activities = [
      ...recentOrders.map((o) => ({
        id: `order-${o.id}`,
        type: 'order',
        title: `New Order #${o.orderNumber}`,
        detail: `$${parseFloat(o.totalPrice).toFixed(2)} — status: ${o.status}`,
        user: o.user ? { name: o.user.name, avatar: o.user.avatar } : null,
        timestamp: o.createdAt,
      })),
      ...recentUsers.map((u) => ({
        id: `user-${u.id}`,
        type: 'registration',
        title: `New User: ${u.name}`,
        detail: u.email,
        user: { name: u.name, avatar: u.avatar },
        timestamp: u.createdAt,
      })),
    ]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, limit);

    res.json({ success: true, data: activities });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/dashboard/reports
 * Business summary report: revenue by period, top products, best customers
 */
router.get('/reports', authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const period = req.query.period || 'month'; // week | month | quarter | year
    const periodMap = { week: 7, month: 30, quarter: 90, year: 365 };
    const days = periodMap[period] || 30;
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const [totalRevRow, orderCount, newUsers, topCats] = await Promise.all([
      // Period revenue
      Order.findOne({
        attributes: [
          [fn('SUM', col('totalPrice')), 'revenue'],
          [fn('COUNT', col('id')), 'orders'],
        ],
        where: { isPaid: true, createdAt: { [Op.gte]: startDate } },
        raw: true,
      }),
      // Total orders in period
      Order.count({ where: { createdAt: { [Op.gte]: startDate } } }),
      // New users in period
      User.count({ where: { createdAt: { [Op.gte]: startDate } } }),
      // Top categories by product count
      Product.findAll({
        attributes: ['category', [fn('COUNT', col('id')), 'count']],
        where: { isActive: true },
        group: ['category'],
        order: [[fn('COUNT', col('id')), 'DESC']],
        limit: 5,
        raw: true,
      }),
    ]);

    // Top paying orders for best customers
    const topOrders = await Order.findAll({
      where: { isPaid: true, createdAt: { [Op.gte]: startDate } },
      include: [{ model: User, as: 'user', attributes: ['id', 'name', 'email'], required: false }],
      order: [['totalPrice', 'DESC']],
      limit: 5,
    });

    const bestCustomers = topOrders
      .filter((o) => o.user)
      .map((o) => ({
        name: o.user.name,
        email: o.user.email,
        userId: o.user.id,
        amount: parseFloat(o.totalPrice),
      }));

    res.json({
      success: true,
      period,
      data: {
        revenue: Math.round(parseFloat(totalRevRow?.revenue || 0) * 100) / 100,
        orders: orderCount,
        newUsers,
        topCategories: topCats.map((c) => ({ category: c.category, count: parseInt(c.count, 10) })),
        bestCustomers,
      },
    });
  } catch (error) {
    next(error);
  }
});

export default router;
