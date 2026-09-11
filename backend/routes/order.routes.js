import express from 'express';
import { Op } from 'sequelize';
import Order from '../models/Order.js';
import Product from '../models/Product.js';
import Notification from '../models/Notification.js';
import User from '../models/User.js';
import { protect, authorize } from '../middleware/auth.js';
import { createOrder, createOrderNotification } from '../services/orderService.js';
import { disarmCartRecovery } from '../services/checkout/recovery.service.js';
import { enqueue, QUEUES } from '../services/queue/queue.service.js';
import cache from '../services/cache/cache.service.js';
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

    const where = {};
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
      where: isNumericId ? { id } : { orderNumber: id },
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

      // Emit real-time notification if socket is available
      const io = req.app.get('io');
      if (io) {
        io.emit('social_proof', {
          type: 'purchase',
          user: req.user.name.split(' ')[0],
          productName: orderItems[0].title,
          time: 'Just now',
        });
      }

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

    const order = await Order.findByPk(req.params.id);
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
 *     summary: Cancel an order
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 */
router.patch('/:id/cancel', protect, async (req, res, next) => {
  try {
    const order = await Order.findByPk(req.params.id);
    if (!order) {
      return res.status(404).json({ success: false, error: 'Order not found' });
    }

    if (req.user.role !== 'admin' && order.user_id !== req.user.id) {
      return res.status(403).json({ success: false, error: 'Not authorized to cancel this order' });
    }

    if (['shipped', 'delivered'].includes(order.status)) {
      return res.status(400).json({
        success: false,
        error: `Cannot cancel order that has already been ${order.status}`,
      });
    }

    await order.update({ status: 'cancelled' });

    // Restore stock for each item
    const orderItems = order.items || [];
    for (const item of orderItems) {
      const product = await Product.findByPk(item.product_id);
      if (product) {
        await product.update({ stock: product.stock + item.quantity });
      }
    }

    logger.info(`Order cancelled: ${order.orderNumber}`);

    res.json({
      success: true,
      message: 'Order cancelled successfully',
      data: order,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/orders/{id}:
 *   delete:
 *     summary: Delete order (Admin only)
 *     tags: [Orders]
 *     security:
 *       - bearerAuth: []
 */
router.delete('/:id', protect, authorize('admin'), async (req, res, next) => {
  try {
    const order = await Order.findByPk(req.params.id);
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
