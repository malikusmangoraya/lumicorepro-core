/**
 * Coupon Service
 * --------------
 * Validate a coupon code and compute its discount against a cart subtotal.
 * Used by the check-out flow (orderService) and the /api/coupons/validate route.
 *
 * Two invariants this module owns:
 *  - a discount is always a finite number in [0, subtotal];
 *  - a limited coupon is consumed with a compare-and-set, never read-then-write,
 *    so two concurrent checkouts cannot both claim the last unit.
 */
import { Op } from 'sequelize';
import Coupon from '../models/Coupon.js';
import Order from '../models/Order.js';

/** DECIMAL columns arrive as strings and a bad row must never yield NaN. */
const num = (value) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

/** Orders that still consume a coupon redemption. */
const NON_CONSUMING_STATUSES = ['cancelled', 'refunded'];

/**
 * Compute discount for a coupon code.
 *
 * @param {string} code - coupon code (case-insensitive)
 * @param {number|null} subtotal - cart items subtotal before shipping/tax; pass
 *   null for a code-only check (a preview with no basket), which skips the
 *   minimum-spend rule and reports a discount of 0.
 * @param {{ userId?: number|null }} [options] - buyer, required for perUserLimit
 * @returns {Promise<{ applied: boolean, discount: number, coupon?: object, error?: string }>}
 */
export async function applyCoupon(code, subtotal, options = {}) {
  if (!code) return { applied: false, discount: 0 };

  const userId = options.userId ?? null;
  const subtotalNum = subtotal === null || subtotal === undefined ? null : num(subtotal);

  const coupon = await Coupon.findOne({
    where: { code: code.toUpperCase().trim(), isActive: true },
  });

  if (!coupon) {
    return { applied: false, discount: 0, error: 'Coupon not found or inactive' };
  }

  const now = new Date();
  if (coupon.startsAt && new Date(coupon.startsAt) > now) {
    return { applied: false, discount: 0, error: 'This coupon is not yet active' };
  }
  if (coupon.expiresAt && new Date(coupon.expiresAt) < now) {
    return { applied: false, discount: 0, error: 'This coupon has expired' };
  }
  if (num(coupon.usageLimit) > 0 && num(coupon.usageCount) >= num(coupon.usageLimit)) {
    return { applied: false, discount: 0, error: 'This coupon has reached its usage limit' };
  }
  if (subtotalNum !== null && num(coupon.minSubtotal) > 0 && subtotalNum < num(coupon.minSubtotal)) {
    return {
      applied: false,
      discount: 0,
      error: `Minimum order subtotal of $${coupon.minSubtotal} required`,
    };
  }

  const perUserLimit = num(coupon.perUserLimit);
  if (userId && perUserLimit > 0) {
    const usedByBuyer = await Order.count({
      where: {
        user_id: userId,
        promoCode: coupon.code,
        status: { [Op.notIn]: NON_CONSUMING_STATUSES },
      },
    });
    if (usedByBuyer >= perUserLimit) {
      return { applied: false, discount: 0, error: 'You have already used this coupon' };
    }
  }

  let discount = 0;

  if (subtotalNum !== null) {
    if (coupon.type === 'percentage') {
      discount = (subtotalNum * num(coupon.value)) / 100;
      if (coupon.maxDiscount !== null && coupon.maxDiscount !== undefined) {
        discount = Math.min(discount, num(coupon.maxDiscount));
      }
    } else if (coupon.type === 'fixed') {
      discount = num(coupon.value);
    } else if (coupon.type === 'free_shipping') {
      // Free-shipping coupons are resolved at checkout (shipping step); discount 0 here.
      discount = 0;
    }

    // A >100% or negative value must not inflate or raise the basket: clamp into
    // [0, subtotal] before rounding.
    discount = Math.min(Math.max(discount, 0), subtotalNum);
  }
  discount = Math.round(discount * 100) / 100;

  return { applied: true, discount, coupon };
}

/**
 * Consume one redemption of a coupon.
 *
 * Limited coupons use a compare-and-set — `UPDATE … WHERE usageCount = <read>` —
 * so a concurrent checkout that already bumped the counter makes this return
 * false instead of over-issuing. Callers must treat `false` as a hard failure
 * and roll the order back.
 *
 * @returns {Promise<boolean>} true when this call took the unit
 */
export async function markCouponUsed(coupon, options = {}) {
  if (!coupon) return false;

  const limit = num(coupon.usageLimit);
  if (limit > 0) {
    const current = num(coupon.usageCount);
    if (current >= limit) return false;
    const [affected] = await Coupon.update(
      { usageCount: current + 1 },
      { where: { id: coupon.id, usageCount: current }, ...options },
    );
    return affected > 0;
  }

  await coupon.increment('usageCount', options);
  return true;
}

export default { applyCoupon, markCouponUsed };
