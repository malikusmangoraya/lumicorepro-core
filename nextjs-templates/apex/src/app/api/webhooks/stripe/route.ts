import { prisma } from '@/lib/prisma';
import { fail, ok, serverError } from '@/lib/api';
import { verifyStripeSignature } from '@/lib/payments';

export const dynamic = 'force-dynamic';

/**
 * POST /api/webhooks/stripe
 *
 * Fail-closed: no secret means 503, a bad or stale signature means 400, and
 * nothing marks an order paid except a verified `checkout.session.completed`.
 */
export async function POST(request: Request) {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!secret) {
    return fail('WEBHOOK_NOT_CONFIGURED', 'STRIPE_WEBHOOK_SECRET is not set', 503);
  }

  // The signature covers the exact bytes Stripe sent, so read the raw text
  // before any JSON parsing.
  const raw = await request.text();
  const signature = request.headers.get('stripe-signature');

  if (!verifyStripeSignature(raw, signature, secret)) {
    return fail('INVALID_SIGNATURE', 'Signature verification failed', 400);
  }

  let event: { id?: string; type?: string; data?: { object?: Record<string, unknown> } };
  try {
    event = JSON.parse(raw);
  } catch {
    return fail('INVALID_JSON', 'Webhook body is not JSON', 400);
  }

  try {
    // Stripe retries; the same event id must not be applied twice.
    if (event.id) {
      const seen = await prisma.webhookEvent.findFirst({ where: { eventId: event.id } });
      if (seen) return ok({ received: true, duplicate: true });
      await prisma.webhookEvent.create({
        data: {
          eventId: event.id,
          eventType: event.type ?? 'unknown',
          gateway: 'stripe',
          payload: raw.slice(0, 8000),
          status: 'received',
        },
      });
    }

    if (event.type === 'checkout.session.completed') {
      const object = event.data?.object ?? {};
      const orderId = (object.client_reference_id as string | undefined) ??
        ((object.metadata as Record<string, string> | undefined)?.orderId);
      const amountTotal = Number(object.amount_total ?? 0);
      const currency = String(object.currency ?? 'usd').toUpperCase();

      if (orderId) {
        const order = await prisma.order.findUnique({ where: { id: orderId } });
        if (order && !order.isPaid) {
          await prisma.order.update({
            where: { id: order.id },
            data: { status: 'paid', isPaid: true, paymentMethod: 'stripe' },
          });
          await prisma.payment.create({
            data: {
              orderId: order.id,
              provider: 'stripe',
              providerRef: String(object.id ?? ''),
              amount: amountTotal / 100,
              currency,
              status: 'succeeded',
            },
          });
        }
      }
    }

    if (event.id) {
      await prisma.webhookEvent.updateMany({
        where: { eventId: event.id },
        data: { status: 'processed' },
      });
    }

    return ok({ received: true });
  } catch {
    return serverError('Could not process the webhook');
  }
}
