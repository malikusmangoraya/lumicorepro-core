import express from 'express';
import { Op } from 'sequelize';
import Product from '../models/Product.js';
import Order from '../models/Order.js';
import Review from '../models/Review.js';
import Booking from '../models/Booking.js';
import { protect, authorize } from '../middleware/auth.js';
import { callerOrgId, tenantWhere } from '../services/tenantScope.service.js';
import { sequelize } from '../config/database.js';
import { enqueue, QUEUES } from '../services/queue/queue.service.js';
import logger from '../utils/logger.js';
import { checkValidation } from '../middleware/validationResult.js';
import {
  TIME_PATTERN,
  isValidDate,
  isPastSlot,
  overlaps,
  slotEnd,
  slotInstant,
} from '../utils/reservationSlot.js';
import { body, param, query } from 'express-validator';

const router = express.Router();

/* ── Helpers ─────────────────────────────────────────────────────────────── */

const menuWhere = (req) => {
  const where = { ...tenantWhere(req, { isActive: true, deleted_at: null }) };
  return where;
};

/**
 * Real-time fan-out over the shared Socket.IO instance.
 *
 * Rooms are identity-scoped (`user:<id>`, `org:<id>`, `role:admin`) and joined
 * only after the socket handshake verifies the JWT against the database, so a
 * customer can never receive another customer's order. No-ops when Socket.IO is
 * absent (unit tests, serverless cold paths) instead of throwing.
 */
const emitRealtime = (req, event, rooms, payload) => {
  const io = req.app?.get?.('io');
  if (!io) return;
  for (const room of rooms) {
    if (room) io.to(room).emit(event, payload);
  }
};

/* ── Public: Menu ───────────────────────────────────────────────────────── */

/**
 * GET /api/restaurant/menu
 * Public menu listing with category, dietary & spicy filters.
 */
router.get(
  '/menu',
  query('category').optional().isString(),
  query('vegetarian').optional().isBoolean(),
  query('vegan').optional().isBoolean(),
  query('spicy').optional().isBoolean(),
  query('minPrice').optional().isFloat({ min: 0 }),
  query('maxPrice').optional().isFloat({ min: 0 }),
  query('search').optional().isString(),
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 50 }),
  checkValidation,
  async (req, res, next) => {
    try {
      const page = parseInt(req.query.page, 10) || 1;
      const limit = parseInt(req.query.limit, 10) || 12;
      const offset = (page - 1) * limit;

      const where = menuWhere(req);

      if (req.query.category && req.query.category !== 'all') {
        where.category = { [Op.iLike]: req.query.category };
      }
      if (req.query.search) {
        where[Op.or] = [
          { title: { [Op.iLike]: `%${req.query.search}%` } },
          { description: { [Op.iLike]: `%${req.query.search}%` } },
        ];
      }
      // Stacked dietary filters must combine: `Op.contains` with every selected
      // tag means the row carries all of them. Assigning one tag per `if` let the
      // last filter silently overwrite the earlier ones.
      const dietary = ['vegetarian', 'vegan', 'spicy'].filter((tag) => req.query[tag] === 'true');
      if (dietary.length) where.tags = { [Op.contains]: dietary };
      // The validators prove these are numeric but leave them as query strings;
      // Postgres rejects a string compared against a numeric column.
      if (req.query.minPrice) where.price = { ...where.price, [Op.gte]: parseFloat(req.query.minPrice) };
      if (req.query.maxPrice) where.price = { ...where.price, [Op.lte]: parseFloat(req.query.maxPrice) };

      const { count: total, rows: items } = await Product.findAndCountAll({
        where,
        order: [['isFeatured', 'DESC'], ['createdAt', 'DESC']],
        limit,
        offset,
      });

      res.json({
        success: true,
        count: items.length,
        total,
        pagination: { page, limit, pages: Math.ceil(total / limit) },
        data: items,
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/restaurant/categories
 * Distinct active menu categories.
 */
router.get('/categories', async (req, res, next) => {
  try {
    const categories = await Product.findAll({
      attributes: [[sequelize.fn('DISTINCT', sequelize.col('category')), 'category']],
      where: { ...tenantWhere(req, { isActive: true }), category: { [Op.ne]: null } },
      raw: true,
    });
    const list = categories.map((c) => c.category).filter(Boolean).sort();
    res.json({ success: true, data: list });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/restaurant/featured
 * Featured menu items (hero specials).
 */
router.get('/featured', async (req, res, next) => {
  try {
    const items = await Product.findAll({
      where: { ...tenantWhere(req, { isActive: true, isFeatured: true }) },
      order: [['createdAt', 'DESC']],
      limit: 8,
    });
    res.json({ success: true, data: items });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/restaurant/menu/:id
 * Single menu item with its reviews.
 */
router.get(
  '/menu/:id',
  param('id').isInt(),
  checkValidation,
  async (req, res, next) => {
    try {
      const item = await Product.findOne({
        where: tenantWhere(req, { id: req.params.id, isActive: true }),
        include: [
          {
            model: Review,
            as: 'reviews',
            order: [['createdAt', 'DESC']],
            limit: 10,
            required: false,
          },
        ],
      });
      if (!item) {
        return res.status(404).json({ success: false, error: 'Menu item not found' });
      }
      res.json({ success: true, data: item });
    } catch (error) {
      next(error);
    }
  }
);

/* ── Public: Orders ─────────────────────────────────────────────────────── */

/**
 * Kitchen-line limits. `items.*.qty` is capped so one cart cannot lock an entire
 * stock counter, and the line count matches the shared checkout's own ceiling
 * (middleware/validations/order.schema.js) so neither vertical can bypass it.
 */
const MAX_ORDER_LINES = 50;
const MAX_QTY_PER_LINE = 99;
const FOOD_PAYMENT_METHODS = ['cod', 'stripe', 'paypal', 'credit_card'];
const FULFILLMENT_TYPES = ['pickup', 'delivery', 'dine_in'];

/** Pickup and dine-in orders ship nothing, so no address is stored for them. */
// express-validator 7 calls an `.if()` condition as (value, meta) where the
// request lives at `meta.req`. Taking the second argument as the request made
// the check always falsy, so every delivery rule was skipped and an order
// shipped with no address.
const isDeliveryOrder = (_value, meta) => meta.req?.body?.fulfillment === 'delivery';

/**
 * Only these keys reach the `shippingAddress` JSONB. An address is echoed back on
 * the invoice, so an arbitrary client object must not be stored verbatim.
 */
const DELIVERY_ADDRESS_FIELDS = ['fullName', 'phone', 'line1', 'line2', 'city', 'state', 'postcode', 'country'];
const deliveryAddress = (address = {}) => {
  const projected = {};
  for (const key of DELIVERY_ADDRESS_FIELDS) {
    if (address[key] !== undefined && address[key] !== null) projected[key] = String(address[key]).trim();
  }
  return projected;
};

/**
 * POST /api/restaurant/orders
 * Create a food order (auth required).
 */
router.post(
  '/orders',
  protect,
  body('items').isArray({ min: 1, max: MAX_ORDER_LINES }),
  body('items.*.productId').isInt({ min: 1 }),
  body('items.*.qty').isInt({ min: 1, max: MAX_QTY_PER_LINE }),
  body('notes').optional().isString().isLength({ max: 500 }),
  body('fulfillment').optional().isIn(FULFILLMENT_TYPES),
  body('paymentMethod').optional().isIn(FOOD_PAYMENT_METHODS),
  body('address').if(isDeliveryOrder).isObject().withMessage('A delivery order needs an address'),
  body('address.fullName').if(isDeliveryOrder).isString().trim().notEmpty(),
  body('address.phone').if(isDeliveryOrder).isString().trim().notEmpty(),
  body('address.line1').if(isDeliveryOrder).isString().trim().notEmpty(),
  body('address.city').if(isDeliveryOrder).isString().trim().notEmpty(),
  body('address.postcode').if(isDeliveryOrder).isString().trim().notEmpty(),
  checkValidation,
  async (req, res, next) => {
    try {
      const { items, notes, fulfillment = 'pickup', paymentMethod = 'cod', address } = req.body;

      // The restaurant cart speaks `{productId, qty}`; services/orderService.js
      // reads `item.product` / `item.quantity`. Translating here is the only
      // place the two vocabularies meet — forwarding the cart keys made every
      // line resolve to `where: { id: undefined }` with a NaN total.
      const orderItems = items.map((i) => ({
        product: Number(i.productId),
        quantity: Number(i.qty),
      }));

      const { createOrder } = await import('../services/orderService.js');
      const { order, totalPrice } = await createOrder(req.user, {
        items: orderItems,
        // `source` is what keeps this vertical's listings and admin mutations
        // away from store orders (constants/orderSources.js).
        source: 'restaurant',
        shippingAddress: fulfillment === 'delivery' ? deliveryAddress(address) : null,
        paymentMethod,
        notes,
        orgId: callerOrgId(req),
      });

      await enqueue(QUEUES.EMAIL, {
        to: req.user.email,
        subject: `Order Confirmed — #${order.orderNumber}`,
        html: `<h2>Order Confirmed</h2><p>Thank you for your order #${order.orderNumber}. Total: $${totalPrice.toFixed(2)}.</p>`,
      });

      logger.info(`Restaurant order created: #${order.orderNumber} by ${req.user.email} ($${totalPrice})`);

      const orgId = callerOrgId(req);
      const event = {
        orderId: order.id,
        orderNumber: order.orderNumber,
        status: order.status,
        totalPrice,
      };
      // Customer tracking page + tenant admin queue, both live. The admin feed is
      // tenant-scoped: org orders go ONLY to that org's room; `role:admin` is
      // reserved for platform (null-org) orders so tenants never see each other.
      emitRealtime(req, 'order:created', [`user:${req.user.id}`], event);
      emitRealtime(req, 'order:new', [orgId != null ? `org:${orgId}` : 'role:admin'], event);

      return res.status(201).json({
        success: true,
        data: { orderNumber: order.orderNumber, id: order.id, status: order.status, totalPrice },
      });
    } catch (error) {
      if (error.statusCode) {
        return res.status(error.statusCode).json({ success: false, error: error.message });
      }
      next(error);
    }
  }
);

/**
 * GET /api/restaurant/orders
 * Current user's food orders (with status tracking).
 */
router.get('/orders', protect, async (req, res, next) => {
  try {
    const rawPage = parseInt(req.query.page, 10);
    const rawLimit = parseInt(req.query.limit, 10);
    // `Math.max(1, parseInt(x) || 1)` is not a clamp: -1 survives it, and a
    // negative LIMIT/OFFSET is a Postgres error (or a NaN offset). Anything
    // non-numeric or non-positive falls back to the defaults.
    const page = rawPage > 0 ? rawPage : 1;
    const limit = rawLimit > 0 ? Math.min(100, rawLimit) : 10;
    const offset = (page - 1) * limit;

    // `source` is the vertical discriminator: without it the caller's store
    // orders appeared in the restaurant history.
    const where = { ...tenantWhere(req), user_id: req.user.id, source: 'restaurant' };

    const { count: total, rows: orders } = await Order.findAndCountAll({
      where,
      order: [['createdAt', 'DESC']],
      limit,
      offset,
    });

    res.json({
      success: true,
      count: orders.length,
      total,
      pagination: { page, limit, pages: Math.ceil(total / limit) },
      data: orders,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/restaurant/orders/:id
 * Single food order with status for tracking.
 */
router.get(
  '/orders/:id',
  protect,
  param('id').isInt({ min: 1 }),
  checkValidation,
  async (req, res, next) => {
    try {
      const order = await Order.findOne({
        where: tenantWhere(req, { id: Number(req.params.id), user_id: req.user.id, source: 'restaurant' }),
      });
      if (!order) {
        return res.status(404).json({ success: false, error: 'Order not found' });
      }
      res.json({ success: true, data: order });
    } catch (error) {
      next(error);
    }
  }
);

/* ── Admin: Order status ───────────────────────────────────────────────── */

const ORDER_STATUSES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'];

/**
 * PATCH /api/restaurant/admin/orders/:id/status
 * Admin moves a food order along the kitchen queue. The restaurant vocabulary is
 * the shared order pipeline's: `processing` is "in the kitchen", `shipped` is
 * "out for delivery / ready at the counter" (see the labels in
 * src/pages/restaurant/AdminDashboard.jsx).
 */
router.patch(
  '/admin/orders/:id/status',
  protect,
  authorize('admin'),
  param('id').isInt({ min: 1 }),
  body('status').isIn(ORDER_STATUSES),
  checkValidation,
  async (req, res, next) => {
    try {
      if (req.body.status === 'cancelled') {
        return res.status(400).json({
          success: false,
          error: 'Use PATCH /api/orders/:id/cancel — it restores stock in one transaction',
        });
      }
      if (req.body.status === 'refunded') {
        return res.status(400).json({
          success: false,
          error: 'Use POST /api/payments/refund — it records the refund with the provider',
        });
      }

      const order = await Order.findOne({
        where: tenantWhere(req, { id: Number(req.params.id), source: 'restaurant' }),
      });
      if (!order) {
        return res.status(404).json({ success: false, error: 'Order not found' });
      }
      await order.update({ status: req.body.status });

      // Push the new status to the ordering customer's tracking view and the
      // tenant admin queue, so neither has to poll.
      emitRealtime(
        req,
        'order:updated',
        [
          `user:${order.user_id}`,
          String(order.user_id),
          order.org_id != null ? `org:${order.org_id}` : 'role:admin',
        ],
        {
          orderId: order.id,
          orderNumber: order.orderNumber,
          status: order.status,
        }
      );

      res.json({ success: true, data: order });
    } catch (error) {
      next(error);
    }
  }
);

/* ── Public: Reservations ───────────────────────────────────────────────── */

/**
 * A seating holds its table for this long, and one tenant may seat this many
 * parties in parallel. Both are per-venue facts the platform cannot know, so
 * they come from the environment with conservative defaults.
 */
const SEATING_MINUTES = Math.max(30, Number(process.env.RESTAURANT_SEATING_MINUTES) || 120);
const TABLE_CAPACITY = Math.max(1, Number(process.env.RESTAURANT_TABLE_CAPACITY) || 8);
const MAX_PARTY_SIZE = Math.max(1, Number(process.env.RESTAURANT_MAX_PARTY_SIZE) || 20);
const RESERVATION_TZ = process.env.RESTAURANT_TIMEZONE || 'UTC';

/**
 * POST /api/restaurant/reservations
 * Book a table.
 */
router.post(
  '/reservations',
  protect,
  body('date').isISO8601().bail().custom(isValidDate).withMessage('Not a real calendar date'),
  body('time').matches(TIME_PATTERN).withMessage('time must be a 24-hour HH:MM'),
  body('partySize').isInt({ min: 1, max: MAX_PARTY_SIZE }),
  body('name').optional().isString().isLength({ max: 100 }),
  body('phone').optional().isString().isLength({ max: 20 }),
  body('notes').optional().isString().isLength({ max: 500 }),
  checkValidation,
  async (req, res, next) => {
    try {
      const { date, time, partySize, name, phone, notes } = req.body;

      // The slot is an instant in the venue's own timezone, never in the
      // server's, so a request means the same table time from any deployment.
      const startAt = slotInstant({ date, time, timeZone: RESERVATION_TZ });
      const endAt = slotEnd(startAt, SEATING_MINUTES);
      if (isPastSlot(startAt)) {
        return res.status(400).json({ success: false, error: 'Reservations must be for a future date and time' });
      }

      const orgId = callerOrgId(req);
      const reservation = await sequelize.transaction(async (t) => {
        // Capacity is checked under the same transaction as the insert: two
        // diners racing for the last table must not both get one. The filter is
        // tenant + calendar day only (JSONB operators would make the query
        // unindexable); the vertical and the overlap are decided below.
        const seated = await Booking.findAll({
          where: {
            ...tenantWhere(req, { date }),
            status: { [Op.notIn]: ['cancelled', 'no-show'] },
          },
          transaction: t,
        });

        const clashing = seated
          .filter((r) => r.metadata?.type === 'restaurant-reservation' && r.startAt)
          .filter((r) => overlaps(startAt, endAt, r.startAt, slotEnd(r.startAt, r.duration || SEATING_MINUTES)));
        if (clashing.some((r) => String(r.user_id) === String(req.user.id))) {
          throw Object.assign(new Error('You already have a reservation at this time'), { statusCode: 409 });
        }
        if (clashing.length >= TABLE_CAPACITY) {
          throw Object.assign(new Error('No table is free at this time'), { statusCode: 409 });
        }

        return Booking.create(
          {
            user_id: req.user.id,
            org_id: orgId,
            service_id: null,
            doctor_id: null,
            date,
            time,
            startAt,
            duration: SEATING_MINUTES,
            reason: `Table reservation for ${partySize}`,
            notes: notes || '',
            status: 'pending',
            metadata: { partySize, phone: phone || null, name: name || null, type: 'restaurant-reservation' },
          },
          { transaction: t }
        );
      });

      emitRealtime(req, 'reservation:created', [orgId != null ? `org:${orgId}` : 'role:admin'], {
        reservationId: reservation.id,
        startAt: reservation.startAt,
        partySize,
        name: name || null,
      });

      res.status(201).json({ success: true, data: reservation });
    } catch (error) {
      if (error.statusCode) {
        return res.status(error.statusCode).json({ success: false, error: error.message });
      }
      next(error);
    }
  }
);

/**
 * GET /api/restaurant/reservations
 * User's reservations.
 */
router.get('/reservations', protect, async (req, res, next) => {
  try {
    const reservations = await Booking.findAll({
      where: { ...tenantWhere(req), user_id: req.user.id, metadata: { [Op.contains]: { type: 'restaurant-reservation' } } },
      order: [['startAt', 'DESC']],
    });
    res.json({ success: true, data: reservations });
  } catch (error) {
    next(error);
  }
});

/* ── Public: Reviews ────────────────────────────────────────────────────── */

/**
 * POST /api/restaurant/reviews
 * Add a rating/review for a menu item.
 */
router.post(
  '/reviews',
  protect,
  body('productId').isInt(),
  body('rating').isInt({ min: 1, max: 5 }),
  body('comment').optional().isString(),
  checkValidation,
  async (req, res, next) => {
    try {
      const { productId, rating, comment } = req.body;

      // Tenant-scoped: a bare findByPk let a caller rate another organization's
      // menu item, and the aggregate below then rewrote that item's rating.
      const product = await Product.findOne({
        where: { id: productId, ...tenantWhere(req) },
      });
      if (!product) {
        return res.status(404).json({ success: false, error: 'Menu item not found' });
      }

      const [review, created] = await Review.findOrCreate({
        where: { user_id: req.user.id, product_id: productId },
        defaults: { rating, comment: comment || '', org_id: callerOrgId(req) },
      });

      if (!created) {
        await review.update({ rating, comment: comment || '' });
      }

      // Recompute aggregate rating.
      const stats = await Review.findAll({
        where: { product_id: productId },
        attributes: [[sequelize.fn('AVG', sequelize.col('rating')), 'avg'], [sequelize.fn('COUNT', '*'), 'cnt']],
        raw: true,
      });
      const avg = parseFloat(stats[0].avg);
      const cnt = parseInt(stats[0].cnt, 10);
      await product.update({ rating: Math.round(avg * 100) / 100, reviewCount: cnt });

      res.status(201).json({ success: true, data: review });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/restaurant/reviews/:productId
 * Reviews for a menu item.
 */
router.get('/reviews/:productId', async (req, res, next) => {
  try {
    const reviews = await Review.findAll({
      where: { product_id: req.params.productId, ...tenantWhere(req) },
      order: [['createdAt', 'DESC']],
      limit: 20,
    });
    res.json({ success: true, data: reviews });
  } catch (error) {
    next(error);
  }
});

/* ── Admin: Menu management ─────────────────────────────────────────────── */

const MENU_WRITABLE = [
  'title', 'description', 'price', 'comparePrice', 'discountPercentage',
  'sku', 'stock', 'category', 'tags', 'images', 'thumbnail', 'attributes',
  'isFeatured', 'isActive',
];

router.post(
  '/admin/menu',
  protect,
  authorize('admin'),
  body('title').notEmpty(),
  body('price').isFloat({ min: 0 }),
  body('category').notEmpty(),
  checkValidation,
  async (req, res, next) => {
    try {
      const payload = {};
      for (const k of MENU_WRITABLE) {
        if (req.body[k] !== undefined) payload[k] = req.body[k];
      }
      payload.org_id = callerOrgId(req);
      const item = await Product.create(payload);
      res.status(201).json({ success: true, data: item });
    } catch (error) {
      next(error);
    }
  }
);

router.patch(
  '/admin/menu/:id',
  protect,
  authorize('admin'),
  param('id').isInt(),
  checkValidation,
  async (req, res, next) => {
    try {
      const item = await Product.findOne({ where: tenantWhere(req, { id: req.params.id }) });
      if (!item) {
        return res.status(404).json({ success: false, error: 'Menu item not found' });
      }
      const payload = {};
      for (const k of MENU_WRITABLE) {
        if (req.body[k] !== undefined) payload[k] = req.body[k];
      }
      await item.update(payload);
      res.json({ success: true, data: item });
    } catch (error) {
      next(error);
    }
  }
);

router.delete(
  '/admin/menu/:id',
  protect,
  authorize('admin'),
  param('id').isInt(),
  checkValidation,
  async (req, res, next) => {
    try {
      const item = await Product.findOne({ where: tenantWhere(req, { id: req.params.id }) });
      if (!item) {
        return res.status(404).json({ success: false, error: 'Menu item not found' });
      }
      await item.destroy();
      res.json({ success: true, message: 'Menu item removed' });
    } catch (error) {
      next(error);
    }
  }
);

/* ── Admin: Stats ───────────────────────────────────────────────────────── */

/**
 * GET /api/restaurant/admin/stats
 * Dashboard stats for the restaurant admin.
 */
router.get('/admin/stats', protect, authorize('admin'), async (req, res, next) => {
  try {
    const baseWhere = tenantWhere(req);
    // Every money figure is restaurant-only: the orders table is shared with the
    // store vertical, so an unfiltered count reported the other product's revenue
    // on this dashboard.
    const orderWhere = { ...baseWhere, source: 'restaurant' };

    const [totalItems, totalOrders, totalRevenue, pendingOrders, totalReservations] =
      await Promise.all([
        Product.count({ where: { ...baseWhere, isActive: true } }),
        Order.count({ where: orderWhere }),
        Order.sum('totalPrice', { where: { ...orderWhere, status: 'delivered' } }) || 0,
        Order.count({ where: { ...orderWhere, status: ['pending', 'processing', 'shipped'] } }),
        Booking.count({ where: { ...baseWhere, metadata: { [Op.contains]: { type: 'restaurant-reservation' } } } }),
      ]);

    res.json({
      success: true,
      data: {
        totalMenuItems: totalItems,
        totalOrders,
        totalRevenue: Number(totalRevenue),
        pendingOrders,
        totalReservations,
      },
    });
  } catch (error) {
    next(error);
  }
});

export default router;
