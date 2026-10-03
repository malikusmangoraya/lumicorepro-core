import express from 'express';
import Order from '../models/Order.js';
import Notification from '../models/Notification.js';
import User from '../models/User.js';
import { protect, authorize } from '../middleware/auth.js';
import { createOrder, createOrderNotification, cancelOrder } from '../services/orderService.js';
import { disarmCartRecovery } from '../services/checkout/recovery.service.js';
import { enqueue, QUEUES } from '../services/queue/queue.service.js';
import { callerOrgId, tenantWhere } from '../services/tenantScope.service.js';
import logger from '../utils/logger.js';
import { validateRequest } from '../middleware/validateRequest.js';
import { createOrderSchema, updateOrderStatusSchema } from '../middleware/validations/index.js';

const router = express.Router();

/**
 * @swagger
 * /api/orders:
 *   get:
 *     summary: Get user orders or all orders (Admin)
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 */
router.get('/', protect, async (req, res, next) => {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 10;
    const offset = (page - 1) * limit;
    const status = req.query.status;

    // Tenant boundary: admins still only see their own organization's orders.
    const where = tenantWhere(req);
    if (req.user.role !== 'admin') {
      where.user_id = req.user.id;
    }
    if (status && status !== 'all') {
      where.status = status;
    }

    const { count: total, rows: orders } = await Order.findAndCountAll({
      where,
      include: [
        {
          model: User,
          as: 'user',
          attributes: ['id', 'name', 'email'],
          required: false,
        },
      ],
      order: [['createdAt', 'DESC']],
      limit,
      offset,
    });

    res.json({
      success: true,
      count: orders.length,
      total,
      pagination: {
        page,
        limit,
        pages: Math.ceil(total / limit),
      },
      data: orders,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/orders/{id}:
 *   get:
 *     summary: Get single order by ID or orderNumber
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 */
router.get('/:id', protect, async (req, res, next) => {
  try {
    const { id } = req.params;
    const isNumericId = /^\d+$/.test(id);

    const order = await Order.findOne({
      where: isNumericId
        ? tenantWhere(req, { id })
        : tenantWhere(req, { orderNumber: id }),
      include: [
        {
          model: User,
          as: 'user',
          attributes: ['id', 'name', 'email', 'phone', 'avatar'],
          required: false,
        },
      ],
    });

    if (!order) {
      return res.status(404).json({ success: false, error: 'Order not found' });
    }

    if (req.user.role !== 'admin' && order.user_id !== req.user.id) {
      return res.status(403).json({ success: false, error: 'Not authorized to view this order' });
    }

    res.json({
      success: true,
      data: order,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/orders:
 *   post:
 *     summary: Create new order
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 */
router.post(
  '/',
  protect,
  validateRequest(createOrderSchema),
  async (req, res, next) => {
    try {
      const { items, shippingAddress, billingAddress, paymentMethod, notes, promoCode } = req.body;

      // Atomic transaction: order-create + stock-decrement, row-locked (FOR UPDATE)
      const { order, orderItems, totalPrice } = await createOrder(req.user, {
        items, shippingAddress, billingAddress, paymentMethod, notes, promoCode,
        orgId: callerOrgId(req),
      });

      // Post-commit, non-transactional notification + cache invalidation
      await createOrderNotification(req.user.id, { orderNumber: order.orderNumber, totalPrice, orderItems });

      // Order placed — the abandoned-checkout recovery window is no longer relevant.
      await disarmCartRecovery(req.user.id).catch(() => {});

      // Post-commit, best-effort confirmation email to customer (via queue)
      await enqueue(QUEUES.EMAIL, {
        to: req.user.email,
        subject: `Order Confirmed — ${order.orderNumber}`,
        html: `<h2>Order Confirmed — ${order.orderNumber}</h2><p>Thank you for your purchase!</p><p>Total: $${totalPrice.toFixed(2)}</p>`,
      });

      // NOTE: a global `social_proof` broadcast lived here. It pushed the
      // buyer's first name + product to every connected socket with no
      // consumer and no consent gate, so it was removed. If social proof is
      // wanted later, emit anonymized product-only events to a public room
      // behind an explicit opt-in preference.

      logger.info(`Order created: ${order.orderNumber} by user ${req.user.email} ($${totalPrice})`);

      return res.status(201).json({
        success: true,
        data: order,
      });
    } catch (error) {
      // Transaction errors carry statusCode for not-found / insufficient-stock
      if (error.statusCode) return res.status(error.statusCode).json({ success: false, error: error.message });
      next(error);
    }
  }
);

/**
 * @swagger
 * /api/orders/{id}/status:
 *   patch:
 *     summary: Update order status (Admin only)
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 */
router.patch('/:id/status', protect, authorize('admin'), validateRequest(updateOrderStatusSchema), async (req, res, next) => {
  try {
    const { status, trackingNumber, carrier } = req.body;

    const order = await Order.findOne({ where: tenantWhere(req, { id: req.params.id }) });
    if (!order) {
      return res.status(404).json({ success: false, error: 'Order not found' });
    }

    const updates = { status };
    if (trackingNumber) updates.trackingNumber = trackingNumber;
    if (carrier) updates.carrier = carrier;
    if (status === 'delivered') {
      updates.isDelivered = true;
      updates.deliveredAt = new Date();
    }

    await order.update(updates);

    // Notify customer
    await Notification.create({
      recipient: order.user_id,
      type: 'order',
      title: `Order Status Updated: ${status.toUpperCase()}`,
      message: `Your order #${order.orderNumber} is now ${status}.`,
      link: `/templates/ecommerce/OrdersHistory`,
      metadata: { orderId: order.id, status },
    });

    res.json({
      success: true,
      data: order,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/orders/{id}/cancel:
 *   patch:
 *     summary: Cancel an order (transactional, idempotent)
 *     description: >
 *       Runs in one transaction with `SELECT ... FOR UPDATE` locks on the order
 *       and on every product it restores. Cancelling an already-cancelled order is
 *       a no-op, so stock is never restored twice. Orders of another organization
 *       answer 404.
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 */
router.patch('/:id/cancel', protect, async (req, res, next) => {
  try {
    const { order, alreadyCancelled } = await cancelOrder(req.params.id, {
      orgId: callerOrgId(req),
      userId: req.user.id,
      isAdmin: req.user.role === 'admin',
    });

    logger.info(`Order ${alreadyCancelled ? 'already cancelled' : 'cancelled'}: ${order.orderNumber}`);

    res.json({
      success: true,
      message: alreadyCancelled ? 'Order was already cancelled' : 'Order cancelled successfully',
      data: order,
    });
  } catch (error) {
    if (error.statusCode) {
      return res.status(error.statusCode).json({ success: false, error: error.message });
    }
    next(error);
  }
});

/**
 * @swagger
 * /api/orders/{id}:
 *   delete:
 *     summary: Delete order (Admin only, soft delete)
 *     description: Sets `deleted_at` (paranoid model); the row is retained.
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 */
router.delete('/:id', protect, authorize('admin'), async (req, res, next) => {
  try {
    const order = await Order.findOne({ where: tenantWhere(req, { id: req.params.id }) });
    if (!order) {
      return res.status(404).json({ success: false, error: 'Order not found' });
    }

    await order.destroy();

    res.json({
      success: true,
      message: 'Order deleted successfully',
    });
  } catch (error) {
    next(error);
  }
});

export default router;
