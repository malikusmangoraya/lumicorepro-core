import { prisma } from '@/lib/prisma';
import { fail, ok, serverError, validate } from '@/lib/api';
import { couponCodeSchema } from '@/lib/validation';
import { discountFor } from '@/lib/coupons';

export const dynamic = 'force-dynamic';

/**
 * GET /api/coupons/validate?code=APEX10&subtotal=500
 *
 * Validation only — nothing is redeemed here. The checkout re-checks the code
 * when the order is written, so a stale or shared answer cannot lower a price.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const parsed = couponCodeSchema.safeParse(searchParams.get('code') ?? '');
  const subtotal = Number(searchParams.get('subtotal') ?? 0);

  if (!parsed.success) return validate(parsed.error.flatten());
  if (!Number.isFinite(subtotal) || subtotal <= 0) {
    return fail('SUBTOTAL_REQUIRED', 'Pass a positive subtotal', 400);
  }

  try {
    const coupon = await prisma.coupon.findUnique({ where: { code: parsed.data } });
    if (!coupon) return fail('COUPON_NOT_FOUND', 'That code does not exist', 404);

    const result = discountFor(coupon, subtotal);
    if (!result.ok) return fail('COUPON_INVALID', result.reason, 409);

    return ok({
      code: result.code,
      discount: result.discount,
      description: result.description,
    });
  } catch {
    return serverError('Could not check the code');
  }
}
