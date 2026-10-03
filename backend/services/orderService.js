/**
 * Order Service — Transactional Checkout
 * --------------------------------------
 * Order-create + inventory-decrement run inside a SINGLE DB transaction with
 * row-level locking (SELECT ... FOR UPDATE) so concurrent requests cannot
 * double-book stock (overselling). Also generates the order number, computes
 * tax/shipping, and records notifications after commit.
 */
import { sequelize as defaultSequelize } from '../config/database.js';
import { Op } from 'sequelize';
import OrderModel from '../models/Order.js';
import ProductModel from '../models/Product.js';
import NotificationModel from '../models/Notification.js';
import CouponModel from '../models/Coupon.js';
import cache from './cache/cache.service.js';
import logger from '../utils/logger.js';
import couponService from './couponService.js';

const TAX_RATE = 0.08;
const FREE_SHIPPING_THRESHOLD = 100;
const STANDARD_SHIPPING = 9.99;

/** Dependency seams — inject fakes in tests, real models by default. */
const deps = {
  sequelize: defaultSequelize,
  Order: OrderModel,
  Product: ProductModel,
  Notification: NotificationModel,
  Coupon: CouponModel,
};

export function _setDeps(overrides) {
  Object.assign(deps, overrides);
}

export function generateOrderNumber() {
  const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const randomStr = Math.random().toString(36).substring(2, 7).toUpperCase();
  return `ORD-${dateStr}-${randomStr}`;
}

/**
 * Create an order atomically. Runs in a transaction, locking each product row
 * (FOR UPDATE) before checking stock to prevent oversell race conditions.
 *
 * `orgId` pins the checkout to one tenant: the product must belong to that org
 * (or be a legacy `org_id IS NULL` row when orgId is null) and the created order
 * is stamped with the same org.
 */
export async function createOrder(user, { items, shippingAddress, billingAddress, paymentMethod, notes, promoCode, currency, orgId }) {
  const { sequelize, Product } = deps;
  return sequelize.transaction(async (t) => {
    let itemsPrice = 0;
    const orderItems = [];
    const stockDeltas = [];
    const orderCurrency = (currency || 'USD').toUpperCase().trim();
    const validCode = /^[A-Z]{3}$/;
    if (!validCode.test(orderCurrency)) {
      const err = new Error(`Unsupported currency: ${orderCurrency}`);
      err.statusCode = 400;
      throw err;
    }

    for (const item of items) {
      // Row-level lock so concurrent checkouts serialize on this product
      const productWhere = { id: item.product };
      if (orgId !== undefined) productWhere.org_id = orgId === null ? { [Op.is]: null } : orgId;
      const product = await Product.findOne({
        where: productWhere,
        lock: t.LOCK.UPDATE,
        transaction: t,
      });
      if (!product) {
        const err = new Error(`Product with ID ${item.product} not found`);
        err.statusCode = 404;
        throw err;
      }

      if (product.stock < item.quantity) {
        const err = new Error(`Insufficient stock for product '${product.title}' (Available: ${product.stock})`);
        err.statusCode = 400;
        throw err;
      }

      const price = parseFloat(product.price);
      const total = price * item.quantity;
      itemsPrice += total;

      orderItems.push({
        product_id: product.id,
        title: product.title,
        price,
        quantity: item.quantity,
        image: item.image || product.thumbnail || (product.images && product.images[0]) || '',
        selectedColor: item.selectedColor || null,
        selectedSize: item.selectedSize || null,
      });

      // Atomic decrement within the same transaction
      await product.update({ stock: product.stock - item.quantity }, { transaction: t });
      stockDeltas.push({ productId: product.id, quantity: item.quantity });
    }

    const taxPrice = Math.round(itemsPrice * TAX_RATE * 100) / 100;
    const shippingPrice = itemsPrice > FREE_SHIPPING_THRESHOLD ? 0 : STANDARD_SHIPPING;

    // Apply promo code discount when provided
    const { applied, discount, coupon, error: couponError } = await couponService.applyCoupon(
      promoCode,
      itemsPrice
    );
    if (promoCode && !applied) {
      const err = new Error(couponError || 'Invalid coupon code');
      err.statusCode = 400;
      throw err;
    }

    const totalPrice = Math.round((itemsPrice + taxPrice + shippingPrice - (discount || 0)) * 100) / 100;
    const orderNumber = generateOrderNumber();

    const order = await deps.Order.create(
      {
        user_id: user.id,
        org_id: orgId === undefined ? null : orgId,
        orderNumber,
        items: orderItems,
        shippingAddress,
        billingAddress: billingAddress || shippingAddress,
        paymentMethod,
        itemsPrice,
        taxPrice,
        shippingPrice,
        discountAmount: discount || 0,
        promoCode: applied ? promoCode.toUpperCase() : null,
        totalPrice,
        currency: orderCurrency,
        notes: notes || '',
        status: 'pending',
      },
      { transaction: t }
    );

    // Mark coupon usage after successful order creation
    if (applied && coupon) {
      await couponService.markCouponUsed(coupon);
    }

    return { order, orderItems, totalPrice, discountAmount: discount || 0 };
  });
}

/**
 * Cancel an order inside one transaction with row-level locks.
 *
 * - Locks the order row (FOR UPDATE) and re-reads its status inside the
 *   transaction, so two concurrent cancels serialize: only the first one
 *   restores stock (idempotent for `cancelled` / `refunded` orders).
 * - Locks each product row (FOR UPDATE) before adding the cancelled quantity
 *   back, so a cancel racing a checkout cannot corrupt the stock counter.
 * - Tenant scoped: `orgId` is part of the lookup, so an order from another org
 *   is reported as `404` rather than `403` (existence is not leaked).
 *
 * @param {string|number} orderId order id (numeric) or order number
 * @param {{orgId?: number|null, userId?: number, isAdmin?: boolean}} [actor]
 * @returns {Promise<{order: object, alreadyCancelled: boolean}>}
 */
export async function cancelOrder(orderId, { orgId, userId, isAdmin = false } = {}) {
  const { sequelize, Product } = deps;
  const raw = String(orderId ?? '').trim();
  const isNumericId = /^\d+$/.test(raw);

  return sequelize.transaction(async (t) => {
    const where = isNumericId ? { id: raw } : { orderNumber: raw };
    if (orgId !== undefined) where.org_id = orgId === null ? { [Op.is]: null } : orgId;

    const order = await deps.Order.findOne({ where, lock: t.LOCK.UPDATE, transaction: t });
    if (!order) {
      const err = new Error('Order not found');
      err.statusCode = 404;
      throw err;
    }

    if (!isAdmin && String(order.user_id) !== String(userId)) {
      const err = new Error('Not authorized to cancel this order');
      err.statusCode = 403;
      throw err;
    }

    if (['shipped', 'delivered'].includes(order.status)) {
      const err = new Error(`Cannot cancel order that has already been ${order.status}`);
      err.statusCode = 400;
      throw err;
    }

    // Status transition is idempotent: a terminal order is never restored twice.
    if (['cancelled', 'refunded'].includes(order.status)) {
      return { order, alreadyCancelled: true };
    }

    await order.update({ status: 'cancelled' }, { transaction: t });

    for (const item of order.items || []) {
      const quantity = Number(item.quantity) || 0;
      if (!item.product_id || quantity <= 0) continue;

      const product = await Product.findOne({
        where: { id: item.product_id },
        lock: t.LOCK.UPDATE,
        transaction: t,
      });
      if (!product) continue;

      await product.update({ stock: product.stock + quantity }, { transaction: t });
    }

    return { order, alreadyCancelled: false };
  });
}

/** Record the post-order notification (after commit, non-transactional). */
export async function createOrderNotification(userId, { orderNumber, totalPrice, orderItems }) {
  await deps.Notification.create({
    recipient: userId,
    type: 'order',
    title: 'Order Placed Successfully',
    message: `Your order #${orderNumber} for $${totalPrice.toFixed(2)} has been placed.`,
    link: '/templates/ecommerce/OrdersHistory',
    metadata: { orderNumber },
  });
  // Invalidate dashboard cache since stats/pending orders changed
  await cache.bust('dashboard');
  return true;
}

export default {
  createOrder,
  cancelOrder,
  generateOrderNumber,
  createOrderNotification,
  logger: (msg, meta) => logger.info(msg, meta),
};