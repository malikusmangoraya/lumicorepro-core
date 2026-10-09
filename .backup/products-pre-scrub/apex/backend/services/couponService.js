/**
 * Coupon Service
 * --------------
 * Validate a coupon code and compute its discount against a cart subtotal.
 * Used by the check-out flow (orderService) and the /api/coupons/validate route.
 */
import Coupon from '../models/Coupon.js';

/**
 * Compute discount for a coupon code.
 * @param {string} code - coupon code (case-insensitive)
 * @param {number} subtotal - cart items subtotal before shipping/tax
 * @returns {Promise<{ applied: boolean, discount: number, coupon?: object, error?: string }>}
 */
export async function applyCoupon(code, subtotal) {
  if (!code) return { applied: false, discount: 0 };

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
  if (coupon.usageLimit > 0 && coupon.usageCount >= coupon.usageLimit) {
    return { applied: false, discount: 0, error: 'This coupon has reached its usage limit' };
  }
  if (parseFloat(coupon.minSubtotal) > 0 && subtotal < parseFloat(coupon.minSubtotal)) {
    return {
      applied: false,
      discount: 0,
      error: `Minimum order subtotal of $${coupon.minSubtotal} required`,
    };
  }

  let discount = 0;
  const subtotalNum = Number(subtotal) || 0;

  if (coupon.type === 'percentage') {
    discount = (subtotalNum * parseFloat(coupon.value)) / 100;
    if (coupon.maxDiscount) {
      discount = Math.min(discount, parseFloat(coupon.maxDiscount));
    }
  } else if (coupon.type === 'fixed') {
    discount = Math.min(parseFloat(coupon.value), subtotalNum);
  } else if (coupon.type === 'free_shipping') {
    // Free-shipping coupons are resolved at checkout (shipping step); discount 0 here.
    discount = 0;
  }

  discount = Math.round(discount * 100) / 100;

  return { applied: true, discount, coupon };
}

/** Increment a coupon's usage counter (called after successful order). */
export async function markCouponUsed(coupon) {
  if (!coupon) return;
  await coupon.increment('usageCount');
}

export default { applyCoupon, markCouponUsed };
