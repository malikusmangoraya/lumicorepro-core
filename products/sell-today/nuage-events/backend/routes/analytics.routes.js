import express from 'express';
import { Op, fn, col, literal } from 'sequelize';
import Order from '../models/Order.js';
import User from '../models/User.js';
import Product from '../models/Product.js';
import { protect, authorize } from '../middleware/auth.js';
import analyticsService from '../services/analyticsService.js';

const router = express.Router();

/**
 * @swagger
 * /api/analytics/dashboard:
 *   get:
 *     summary: Get dashboard KPIs & summary stats
 *     tags: [Analytics]
 *     security:
 *       - bearerAuth: []
 */
router.get('/dashboard', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const [totalUsers, totalProducts, totalOrders, lowStockProducts] = await Promise.all([
      User.count(),
      Product.count({ where: { isActive: true } }),
      Order.count(),
      Product.count({ where: { stock: { [Op.lte]: 5 }, isActive: true } }),
    ]);

    // Revenue aggregation using Sequelize
    const revenueResult = await Order.findOne({
      attributes: [
        [fn('SUM', col('totalPrice')), 'totalRevenue'],
        [fn('AVG', col('totalPrice')), 'avgOrderValue'],
      ],
      where: { isPaid: true },
      raw: true,
    });

    const totalRevenue = parseFloat(revenueResult?.totalRevenue || 0);
    const avgOrderValue = parseFloat(revenueResult?.avgOrderValue || 0);

    // Recent 5 orders
    const recentOrders = await Order.findAll({
      include: [
        {
          model: User,
          as: 'user',
          attributes: ['id', 'name', 'email', 'avatar'],
          required: false,
        },
      ],
      order: [['createdAt', 'DESC']],
      limit: 5,
    });

    res.json({
      success: true,
      data: {
        kpis: {
          totalRevenue: Math.round(totalRevenue * 100) / 100,
          totalOrders,
          totalUsers,
          totalProducts,
          lowStockProducts,
          avgOrderValue: Math.round(avgOrderValue * 100) / 100,
          conversionRate: totalUsers > 0 ? Math.round((totalOrders / totalUsers) * 100) / 100 : 0,
        },
        recentOrders,
      },
    });
  } catch (error) {
    next(error);
  }
});

// Alias for /api/analytics/stats
router.get('/stats', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const [totalUsers, totalProducts, totalOrders, revenueResult] = await Promise.all([
      User.count(),
      Product.count({ where: { isActive: true } }),
      Order.count(),
      Order.findOne({
        attributes: [[fn('SUM', col('totalPrice')), 'totalRevenue']],
        where: { isPaid: true },
        raw: true,
      }),
    ]);

    res.json({
      success: true,
      data: {
        totalUsers,
        totalProducts,
        totalOrders,
        totalRevenue: parseFloat(revenueResult?.totalRevenue || 0),
      },
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/analytics/sales:
 *   get:
 *     summary: Get sales revenue history per day
 *     tags: [Analytics]
 *     security:
 *       - bearerAuth: []
 */
router.get('/sales', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const days = parseInt(req.query.days, 10) || 30;
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const salesTimeline = await Order.findAll({
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

    res.json({
      success: true,
      data: salesTimeline.map((row) => ({
        date: row.date,
        revenue: Math.round(parseFloat(row.revenue || 0) * 100) / 100,
        orders: parseInt(row.orders, 10),
      })),
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/analytics/top-products:
 *   get:
 *     summary: Get bestselling products based on order items
 *     tags: [Analytics]
 *     security:
 *       - bearerAuth: []
 */
router.get('/top-products', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit, 10) || 5;
    const days = parseInt(req.query.days, 10) || 90;

    // Use a single SQL pass (window function) instead of loading every order
    let rows;
    try {
      rows = await analyticsService.topProducts({ days, limit });
    } catch (err) {
      // Fallback to the previous in-JS aggregation if DB/CTE unavailable
      const orders = await Order.findAll({ attributes: ['items'], raw: true });
      const productMap = {};
      for (const order of orders) {
        for (const item of order.items || []) {
          const key = item.product_id || item.product || item.title;
          if (!productMap[key]) {
            productMap[key] = {
              productId: key,
              title: item.title,
              image: item.image || '',
              totalUnitsSold: 0,
              totalRevenue: 0,
            };
          }
          productMap[key].totalUnitsSold += item.quantity || 0;
          productMap[key].totalRevenue += (item.price || 0) * (item.quantity || 0);
        }
      }
      rows = Object.values(productMap)
        .sort((a, b) => b.totalUnitsSold - a.totalUnitsSold)
        .slice(0, limit);
    }

    res.json({
      success: true,
      data: rows.map((p) => ({
        ...p,
        totalRevenue: Math.round(Number(p.totalRevenue || p.gross || 0) * 100) / 100,
        totalUnitsSold: Number(p.totalUnitsSold ?? p.units ?? 0),
      })),
    });
  } catch (error) {
    next(error);
  }
});

router.get('/revenue-report', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const days = parseInt(req.query.days, 10) || 30;
    const report = await analyticsService.revenueReport({ days });
    res.json({ success: true, days, data: report });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/analytics/user-growth:
 *   get:
 *     summary: Get user registration growth by month
 *     tags: [Analytics]
 *     security:
 *       - bearerAuth: []
 */
router.get('/user-growth', protect, authorize('admin'), async (req, res, next) => {
  try {
    const userGrowth = await User.findAll({
      attributes: [
        [fn('TO_CHAR', col('createdAt'), 'YYYY-MM'), 'month'],
        [fn('COUNT', col('id')), 'newUsers'],
      ],
      group: [fn('TO_CHAR', col('createdAt'), 'YYYY-MM')],
      order: [[fn('TO_CHAR', col('createdAt'), 'YYYY-MM'), 'ASC']],
      raw: true,
    });

    res.json({
      success: true,
      data: userGrowth.map((row) => ({
        month: row.month,
        newUsers: parseInt(row.newUsers, 10),
      })),
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/analytics/category-distribution:
 *   get:
 *     summary: Get product distribution by category
 *     tags: [Analytics]
 */
router.get('/category-distribution', async (req, res, next) => {
  try {
    const categories = await Product.findAll({
      attributes: [
        'category',
        [fn('COUNT', col('id')), 'count'],
        [fn('AVG', col('price')), 'avgPrice'],
      ],
      where: { isActive: true },
      group: ['category'],
      order: [[fn('COUNT', col('id')), 'DESC']],
      raw: true,
    });

    res.json({
      success: true,
      data: categories.map((c) => ({
        category: c.category,
        count: parseInt(c.count, 10),
        avgPrice: Math.round(parseFloat(c.avgPrice || 0) * 100) / 100,
      })),
    });
  } catch (error) {
    next(error);
  }
});

export default router;
