/**
 * Order Service — Transactional Checkout
 * --------------------------------------
 * Order-create + inventory-decrement run inside a SINGLE DB transaction with
 * row-level locking (SELECT ... FOR UPDATE) so concurrent requests cannot
 * double-book stock (overselling). Also generates the order number, computes
 * tax/shipping, and records notifications after commit.
 */
import { sequelize as defaultSequelize } from '../config/database.js';
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
 */
export async function createOrder(user, { items, shippingAddress, billingAddress, paymentMethod, notes, promoCode, currency }) {
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
      const product = await Product.findOne({
        where: { id: item.product },
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
  generateOrderNumber,
  createOrderNotification,
  logger: (msg, meta) => logger.info(msg, meta),
};