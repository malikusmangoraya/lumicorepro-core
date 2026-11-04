/**
 * Coupon maths, kept pure so the rules can be tested and so the API and the
 * checkout UI cannot disagree about what a code is worth.
 */

export type CouponLike = {
  code: string;
  type: string; // percent | fixed
  value: number;
  minSubtotal: number | null;
  maxDiscount: number | null;
  usageLimit: number | null;
  usedCount: number;
  startsAt: Date | null;
  expiresAt: Date | null;
  isActive: boolean;
};

export type CouponResult =
  | { ok: true; code: string; discount: number; description: string }
  | { ok: false; reason: string };

const round = (value: number) => Math.round(value * 100) / 100;

export function discountFor(coupon: CouponLike, subtotal: number, now = new Date()): CouponResult {
  if (!coupon.isActive) return { ok: false, reason: 'That code is no longer active' };
  if (coupon.startsAt && coupon.startsAt > now) {
    return { ok: false, reason: 'That code is not active yet' };
  }
  if (coupon.expiresAt && coupon.expiresAt < now) {
    return { ok: false, reason: 'That code has expired' };
  }
  if (coupon.usageLimit !== null && coupon.usedCount >= coupon.usageLimit) {
    return { ok: false, reason: 'That code has been fully redeemed' };
  }
  if (coupon.minSubtotal !== null && subtotal < coupon.minSubtotal) {
    return {
      ok: false,
      reason: `That code needs a subtotal of at least ${coupon.minSubtotal}`,
    };
  }

  let discount =
    coupon.type === 'percent'
      ? (subtotal * Math.min(100, Math.max(0, coupon.value))) / 100
      : Math.min(subtotal, Math.max(0, coupon.value));

  if (coupon.maxDiscount !== null) discount = Math.min(discount, coupon.maxDiscount);
  discount = round(Math.min(discount, subtotal));

  if (discount <= 0) return { ok: false, reason: 'That code is worth nothing on this order' };

  return {
    ok: true,
    code: coupon.code,
    discount,
    description:
      coupon.type === 'percent'
        ? `${coupon.value}% off`
        : `${coupon.value} off the subtotal`,
  };
}
