import crypto from 'node:crypto';

/**
 * Stripe Checkout without the SDK.
 *
 * Two calls are needed: create a session, and verify the webhook signature.
 * Both are small enough to write against the documented REST API, which keeps
 * ~500 KB of SDK out of a template that may never enable payments.
 *
 * Fail-closed rules, learned the hard way elsewhere in this repo:
 *  - a missing secret is a 503, never "skip verification";
 *  - the signature is computed over the RAW body, never a parsed one;
 *  - a timestamp outside the tolerance is rejected (replay protection).
 */

const API = 'https://api.stripe.com/v1';

export function stripeConfigured(): boolean {
  return Boolean(process.env.STRIPE_SECRET_KEY && process.env.STRIPE_WEBHOOK_SECRET);
}

export type CheckoutSessionInput = {
  orderId: string;
  orderNumber: string;
  amount: number;
  currency: string;
  email: string;
  origin: string;
};

export async function createStripeCheckoutSession(
  input: CheckoutSessionInput,
): Promise<{ url: string } | { error: string }> {
  const secret = process.env.STRIPE_SECRET_KEY;
  if (!secret) return { error: 'payment-not-configured' };

  const body = new URLSearchParams();
  body.set('mode', 'payment');
  body.set('success_url', `${input.origin}/checkout/success?order=${encodeURIComponent(input.orderNumber)}`);
  body.set('cancel_url', `${input.origin}/checkout?cancelled=1`);
  body.set('customer_email', input.email);
  body.set('client_reference_id', input.orderId);
  body.set('metadata[orderId]', input.orderId);
  body.set('metadata[orderNumber]', input.orderNumber);
  body.set('line_items[0][quantity]', '1');
  body.set('line_items[0][price_data][currency]', input.currency.toLowerCase());
  body.set('line_items[0][price_data][unit_amount]', String(Math.round(input.amount * 100)));
  body.set('line_items[0][price_data][product_data][name]', `Order ${input.orderNumber}`);

  try {
    const response = await fetch(`${API}/checkout/sessions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${secret}`,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Stripe-Version': '2024-06-20',
      },
      body,
    });

    if (!response.ok) {
      const detail = (await response.json().catch(() => null)) as { error?: { message?: string } } | null;
      return { error: detail?.error?.message ?? `stripe ${response.status}` };
    }

    const session = (await response.json()) as { url?: string };
    if (!session.url) return { error: 'stripe returned no url' };
    return { url: session.url };
  } catch {
    return { error: 'could not reach stripe' };
  }
}

/** Stripe's `t=…,v1=…` header, checked against the raw request body. */
export function verifyStripeSignature(
  rawBody: string,
  header: string | null,
  secret: string | undefined,
  toleranceSeconds = 300,
): boolean {
  if (!secret || !header) return false;

  const parts = header.split(',').reduce<Record<string, string>>((acc, part) => {
    const [key, value] = part.split('=');
    if (key && value) acc[key.trim()] = value.trim();
    return acc;
  }, {});

  const timestamp = Number(parts.t);
  const signature = parts.v1;
  if (!Number.isFinite(timestamp) || !signature) return false;

  const age = Math.abs(Math.floor(Date.now() / 1000) - timestamp);
  if (age > toleranceSeconds) return false;

  const expected = crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${rawBody}`, 'utf8')
    .digest('hex');

  const a = Buffer.from(expected, 'utf8');
  const b = Buffer.from(signature, 'utf8');
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}
