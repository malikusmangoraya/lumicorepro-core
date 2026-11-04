import { prisma } from '@/lib/prisma';
import { created, fail, forbidden, notFound, serverError, unauthorized } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { createStripeCheckoutSession, stripeConfigured } from '@/lib/payments';

export const dynamic = 'force-dynamic';

/**
 * POST /api/payments/checkout — start a hosted card payment for an order.
 *
 * A guest proves ownership with the email the order was placed under; a signed
 * in customer must own the order. This is not an authentication boundary for
 * money — Stripe charges the card and the webhook is what marks the order paid.
 */
export async function POST(request: Request) {
  if (!stripeConfigured()) {
    return fail(
      'PAYMENT_NOT_CONFIGURED',
      'Card payments are not configured. Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET.',
      503,
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const { orderId, email } = (body ?? {}) as { orderId?: string; email?: string };
  if (!orderId) return fail('ORDER_REQUIRED', 'Send the order id', 400);

  const session = await getSession().catch(() => null);
  if (!session && !email) return unauthorized('Send the order email to pay as a guest');

  try {
    const order = await prisma.order.findUnique({ where: { id: orderId } });
    if (!order) return notFound('Order');

    const owns = session?.role === 'admin' || (session && order.userId === session.id);
    const emailMatches =
      typeof email === 'string' && email.toLowerCase() === order.customerEmail.toLowerCase();
    if (!owns && !emailMatches) return forbidden('That order is not yours');

    if (order.isPaid || order.status !== 'pending') {
      return fail('ALREADY_PAID', 'This order is not awaiting payment', 409);
    }

    const origin = new URL(request.url).origin;
    const result = await createStripeCheckoutSession({
      orderId: order.id,
      orderNumber: order.orderNumber,
      amount: order.total,
      currency: order.currency,
      email: order.customerEmail,
      origin,
    });

    if ('error' in result) {
      return fail('PAYMENT_PROVIDER_ERROR', result.error, 502);
    }

    return created({ url: result.url }, 'Checkout session created');
  } catch {
    return serverError('Could not start the payment');
  }
}
