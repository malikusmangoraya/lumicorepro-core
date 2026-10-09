/**
 * Payment gateway client.
 * ----------------------
 * The browser never sees a gateway secret and never handles card data: this module talks to
 * the app's own Express backend, which is the only place a secret is read, and the browser is
 * then redirected to the gateway's hosted checkout page.
 *
 * Endpoints (see backend/routes/payment.routes.js and backend/routes/lemonsqueezy.routes.js):
 *   GET  /api/payment/config          which gateways are live, plus publishable keys
 *   POST /api/payment/checkout        Stripe Checkout session for a plan or an order
 *   POST /api/payment/portal          Stripe Billing Portal (subscription management)
 *   GET  /api/lemonsqueezy/config     merchant-of-record storefront config
 *   POST /api/lemonsqueezy/checkout   Lemon Squeezy hosted checkout (works signed out)
 *
 * A gateway that is not configured answers 503 with `configured: false`; that surfaces here
 * as PaymentNotConfiguredError, so a storefront can tell "no keys yet" apart from "broken"
 * instead of silently showing a demo dialog.
 */
import { getApiConfig } from '../services/apiConfig';

const { API_URL } = getApiConfig();

export const GATEWAYS = {
  stripe: 'stripe',
  paypal: 'paypal',
  paddle: 'paddle',
  lemonsqueezy: 'lemonsqueezy',
};

export class PaymentNotConfiguredError extends Error {
  constructor(message) {
    super(message || 'Online payment is not configured for this deployment yet.');
    this.name = 'PaymentNotConfiguredError';
    this.code = 'PAYMENT_UNCONFIGURED';
  }
}

export class PaymentRequestError extends Error {
  constructor(message, options) {
    super(message || 'The payment service could not complete the request.');
    this.name = 'PaymentRequestError';
    this.code = options?.status ? `PAYMENT_HTTP_${options.status}` : 'PAYMENT_REQUEST_FAILED';
  }
}

const authToken = () => {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage.getItem('auth_token');
  } catch {
    return null;
  }
};

async function request(path, { method = 'GET', body } = {}) {
  const token = authToken();
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: {
        Accept: 'application/json',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  } catch (cause) {
    throw new PaymentRequestError(
      'Could not reach the payment service. Check your connection and try again.',
      { cause }
    );
  }

  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = {};
  }

  if (response.status === 503 || payload.configured === false) {
    throw new PaymentNotConfiguredError(
      payload.error || payload.unconfiguredMessage || 'Online payment is not configured yet.'
    );
  }
  if (!response.ok) {
    throw new PaymentRequestError(
      payload.error || `The payment service rejected the request (HTTP ${response.status}).`,
      { status: response.status }
    );
  }
  return payload;
}

export const paymentProvider = {
  /** Which gateways this deployment actually has keys for. */
  async getConfig() {
    return request('/payment/config');
  },

  /** Merchant-of-record storefront config (store id, whether the webhook is verified). */
  async getLemonSqueezyConfig() {
    try {
      return await request('/lemonsqueezy/config');
    } catch (error) {
      if (error instanceof PaymentNotConfiguredError) return { configured: false };
      throw error;
    }
  },

  /** Stripe Checkout session. Resolves to the hosted URL to send the buyer to. */
  async createStripeCheckout({ planId, orderId, successUrl, cancelUrl, agentApiKey } = {}) {
    const payload = await request('/payment/checkout', {
      method: 'POST',
      body: { planId, orderId, successUrl, cancelUrl, agentApiKey },
    });
    return { gateway: GATEWAYS.stripe, url: payload.checkoutUrl, sessionId: payload.sessionId, mode: payload.mode };
  },

  /** Lemon Squeezy hosted checkout. Works for signed-out visitors. */
  async createLemonSqueezyCheckout({
    variantId,
    planName,
    amount,
    currency,
    orderId,
    email,
    redirectUrl,
    customData,
  } = {}) {
    const payload = await request('/lemonsqueezy/checkout', {
      method: 'POST',
      body: { variantId, planName, amount, currency, orderId, email, redirectUrl, customData },
    });
    return { gateway: GATEWAYS.lemonsqueezy, url: payload.url, mode: payload.mode, paymentId: payload.paymentId };
  },

  /** Stripe Billing Portal, for changing or cancelling an existing subscription. */
  async createPortalSession() {
    const payload = await request('/payment/portal', { method: 'POST', body: {} });
    return { url: payload.url };
  },

  /**
   * Picks a configured gateway and opens its checkout.
   *
   * `gateway: 'auto'` prefers Stripe for signed-in buyers (it can attach the payment to
   * their account) and Lemon Squeezy otherwise, because its route accepts anonymous buyers.
   */
  async createCheckoutSession(options = {}) {
    const { gateway = 'auto', amount, currency, planName, orderId, email, successUrl, cancelUrl } = options;
    const signedIn = Boolean(authToken());

    const wantsStripe = gateway === GATEWAYS.stripe || (gateway === 'auto' && signedIn);
    const attempts = wantsStripe
      ? [
          () => this.createStripeCheckout({ planId: options.planId, orderId, successUrl, cancelUrl }),
          () => this.createLemonSqueezyCheckout({ variantId: options.variantId, planName, amount, currency, orderId, email }),
        ]
      : [
          () => this.createLemonSqueezyCheckout({ variantId: options.variantId, planName, amount, currency, orderId, email }),
          () => this.createStripeCheckout({ planId: options.planId, orderId, successUrl, cancelUrl }),
        ];

    const failures = [];
    for (const attempt of attempts) {
      try {
        const session = await attempt();
        if (session?.url) return session;
        failures.push('the gateway returned no checkout URL');
      } catch (error) {
        failures.push(error.message);
      }
    }

    throw new PaymentNotConfiguredError(
      failures.filter(Boolean).join(' ') || 'No payment gateway is configured for this deployment.'
    );
  },
};

export default paymentProvider;
