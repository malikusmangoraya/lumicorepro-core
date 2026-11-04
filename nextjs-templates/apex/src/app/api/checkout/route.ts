import { prisma } from '@/lib/prisma';
import { created, fail, serverError, tooMany, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { checkoutSchema } from '@/lib/validation';
import { calculateTotals } from '@/lib/orders';
import { clientIp, rateLimit } from '@/lib/rate-limit';
import { orderNumber } from '@/lib/utils';
import { discountFor } from '@/lib/coupons';
import { orderConfirmationEmail, sendEmail } from '@/lib/email';

export const dynamic = 'force-dynamic';

/**
 * POST /api/checkout — guest or signed-in.
 *
 * Prices and availability come from the database, never from the cart the
 * browser sent: the client only says *what* and *how many*. Stock is claimed
 * with a conditional update so two buyers cannot take the last item.
 */
export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`checkout:${ip}`, 10, 60 * 60 * 1000);
  if (!limit.allowed) {
    const response = tooMany('Too many checkout attempts. Try again later.');
    response.headers.set('Retry-After', String(limit.retryAfter));
    return response;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = checkoutSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  const input = parsed.data;
  const session = await getSession().catch(() => null);

  try {
    const lines: {
      title: string;
      unitPrice: number;
      quantity: number;
      productId: string | null;
      vehicleId: string | null;
    }[] = [];

    for (const item of input.items) {
      if (item.kind === 'vehicle') {
        const vehicle = await prisma.vehicle.findUnique({ where: { slug: item.slug } });
        if (!vehicle || !['active', 'reserved'].includes(vehicle.status)) {
          return fail('UNAVAILABLE', `"${item.slug}" is no longer available`, 409);
        }
        if (item.quantity > 1) {
          return fail('INVALID_QUANTITY', 'A vehicle can only be reserved once', 422);
        }
        lines.push({
          title: vehicle.title,
          unitPrice: vehicle.price,
          quantity: 1,
          productId: null,
          vehicleId: vehicle.id,
        });
        continue;
      }

      const product = await prisma.product.findUnique({ where: { slug: item.slug } });
      if (!product || !product.isActive) {
        return fail('UNAVAILABLE', `"${item.slug}" is no longer available`, 409);
      }
      if (product.stock < item.quantity) {
        return fail(
          'OUT_OF_STOCK',
          `Only ${product.stock} left of ${product.title}`,
          409,
        );
      }
      lines.push({
        title: product.title,
        unitPrice: product.price,
        quantity: item.quantity,
        productId: product.id,
        vehicleId: null,
      });
    }

    // A coupon is re-validated here against the server's own subtotal: the
    // browser only names the code, it never sends a discount amount.
    let discount = 0;
    let couponCode: string | null = null;
    if (input.couponCode) {
      const subtotal = lines.reduce((sum, line) => sum + line.unitPrice * line.quantity, 0);
      const coupon = await prisma.coupon.findUnique({ where: { code: input.couponCode } });
      if (!coupon) return fail('COUPON_NOT_FOUND', 'That discount code does not exist', 404);
      const result = discountFor(coupon, subtotal);
      if (!result.ok) return fail('COUPON_INVALID', result.reason, 409);
      discount = result.discount;
      couponCode = coupon.code;
    }

    const totals = calculateTotals(
      lines.map((line) => ({ unitPrice: line.unitPrice, quantity: line.quantity })),
      { discount },
    );

    const currency = lines.length > 0 ? 'USD' : 'USD';
    const emailUser = await prisma.user.findUnique({ where: { email: input.email } });

    let order: Awaited<ReturnType<typeof prisma.order.create>> | null = null;
    for (let attempt = 0; attempt < 5 && !order; attempt += 1) {
      const seq = (await prisma.order.count()) + 1 + attempt;
      try {
        order = await prisma.order.create({
          data: {
            orderNumber: orderNumber(seq),
            userId: session?.id ?? emailUser?.id ?? null,
            customerEmail: input.email,
            shippingAddress: JSON.stringify({
              ...input.address,
              name: input.name,
              phone: input.phone || undefined,
            }),
            billingAddress: JSON.stringify(input.address),
            subtotal: totals.subtotal,
            tax: totals.tax,
            shipping: totals.shipping,
            discount: totals.discount,
            total: totals.total,
            currency,
            status: 'pending',
            notes: input.notes,
            couponCode,
            items: {
              create: lines.map((line) => ({
                productId: line.productId,
                title: line.title,
                unitPrice: line.unitPrice,
                quantity: line.quantity,
                lineTotal: Math.round(line.unitPrice * line.quantity * 100) / 100,
              })),
            },
          },
          include: { items: true },
        });
      } catch (error) {
        const code = (error as { code?: string }).code;
        if (code !== 'P2002' || attempt === 4) throw error;
      }
    }

    if (!order) return serverError('Could not allocate an order number');

    // Claim stock only after the order exists, and only if it is still there.
    for (const line of lines) {
      if (!line.productId) continue;
      const claimed = await prisma.product.updateMany({
        where: { id: line.productId, stock: { gte: line.quantity } },
        data: { stock: { decrement: line.quantity } },
      });
      if (claimed.count === 0) {
        await prisma.order.update({ where: { id: order.id }, data: { status: 'cancelled' } });
        return fail('OUT_OF_STOCK', `${line.title} sold out while you were checking out`, 409);
      }
    }

    // Fire-and-forget: a mail failure must never fail a placed order.
    void sendEmail(
      orderConfirmationEmail({
        to: order.customerEmail,
        orderNumber: order.orderNumber,
        total: order.total,
        currency: order.currency,
      }),
    );

    if (couponCode) {
      await prisma.coupon.update({
        where: { code: couponCode },
        data: { usedCount: { increment: 1 } },
      });
    }

    return created(
      {
        id: order.id,
        orderNumber: order.orderNumber,
        total: order.total,
        discount: order.discount,
        currency: order.currency,
        email: order.customerEmail,
      },
      'Order placed',
    );
  } catch {
    return serverError('Could not place the order');
  }
}
