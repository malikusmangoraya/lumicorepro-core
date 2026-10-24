import Stripe from 'stripe';
import { getGatewayConfig } from './config.js';
import { getStripeClient, getStripePublishableKey } from './dynamic.js';
import Payment from '../../models/Payment.js';
import logger from '../../utils/logger.js';

class StripeService {
  constructor() {
    const config = getGatewayConfig('stripe');
    this.enabled = config?.enabled || false;
    this.client = config?.enabled ? new Stripe(config.secretKey) : null;
    this.name = 'Stripe';
    this.description = 'Credit card & digital wallet payments (Global)';
    this.supportedCurrencies = ['usd', 'eur', 'gbp', 'cad', 'aud', 'jpy', 'inr', 'pkr', 'bdt', 'try', 'php', 'idr', 'myr', 'sgd'];
    this.region = 'Global';
    this.icon = '💳';
  }

  /** Stripe amounts are minor units; zero-decimal currencies must not ×100. */
  _toMinorUnits(amount, currency = 'usd') {
    const zeroDecimal = new Set(['bif', 'clp', 'djf', 'gnf', 'jpy', 'kmf', 'krw', 'mga', 'pyg', 'rwf', 'ugx', 'vnd', 'vuv', 'xaf', 'xof', 'xpf']);
    return Math.round(zeroDecimal.has(String(currency).toLowerCase()) ? amount : amount * 100);
  }

  /**
   * Re-initialize the client from runtime SystemConfig (called after the admin
   * saves new keys). Keeps the singleton in sync without a restart.
   */
  async refresh() {
    const client = await getStripeClient();
    this.client = client;
    this.enabled = !!client;
    this.publishableKey = await getStripePublishableKey();
    return { enabled: this.enabled };
  }

  async createPayment({ amount, currency = 'usd', orderId, description, metadata = {} }) {
    if (!this.enabled) {
      // Mock mode for development
      const paymentIntentId = `pi_mock_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
      return {
        id: paymentIntentId,
        clientSecret: `${paymentIntentId}_secret_mock`,
        amount,
        currency,
        mock: true,
      };
    }

    const paymentIntent = await this.client.paymentIntents.create({
      amount: this._toMinorUnits(amount, currency),
      currency,
      description,
      metadata: {
        orderId: orderId?.toString() || '',
        ...metadata,
      },
    });

    return {
      id: paymentIntent.id,
      clientSecret: paymentIntent.client_secret,
      amount,
      currency,
      mock: false,
    };
  }

  async confirmPayment({ paymentIntentId, orderId }) {
    if (!this.enabled) return { success: true, mock: true, paymentIntentId };

    const paymentIntent = await this.client.paymentIntents.retrieve(paymentIntentId);
    return {
      success: paymentIntent.status === 'succeeded',
      paymentIntentId: paymentIntent.id,
      status: paymentIntent.status,
    };
  }

  async refund({ paymentId, amount, reason, currency = 'usd' }) {
    if (!this.enabled) {
      return { success: true, mock: true, paymentId };
    }

    // `amount: 0` must not silently become a FULL refund (0 is falsy).
    if (amount === 0) {
      throw new Error('Stripe refund: amount must be greater than zero (omit it for a full refund)');
    }

    const refund = await this.client.refunds.create({
      payment_intent: paymentId,
      amount: amount ? this._toMinorUnits(amount, currency) : undefined,
      reason: reason || 'requested_by_customer',
    });

    return { success: true, refundId: refund.id, paymentId };
  }

  async handleWebhook(event) {
    switch (event.type) {
      case 'payment_intent.succeeded': {
        const pi = event.data.object;
        await Payment.update(
          { status: 'succeeded', gatewayPaymentId: pi.id },
          { where: { stripePaymentIntentId: pi.id } }
        );
        break;
      }
      case 'payment_intent.payment_failed': {
        const pi = event.data.object;
        await Payment.update(
          { status: 'failed' },
          { where: { stripePaymentIntentId: pi.id } }
        );
        break;
      }
      default:
        logger.info(`Unhandled Stripe webhook: ${event.type}`);
    }
  }

  getPublicKey() {
    if (this.publishableKey) return this.publishableKey;
    return process.env.STRIPE_PUBLISHABLE_KEY || 'pk_test_placeholder';
  }

  async ensureCustomer(user) {
    if (!this.enabled) return { id: `cus_mock_${user?.id || 'anon'}` };
    if (user?.stripeCustomerId) return { id: user.stripeCustomerId, exists: true };
    const customer = await this.client.customers.create({
      email: user?.email,
      name: user?.name,
      metadata: { userId: String(user?.id || '') },
    });
    return { id: customer.id };
  }

  async createCheckoutSession({
    user,
    priceId,
    mode = 'subscription',
    successUrl,
    cancelUrl,
    metadata = {},
    credits = 0,
  }) {
    const { id: customerId } = await this.ensureCustomer(user);
    const params = {
      mode,
      customer: customerId,
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: successUrl,
      cancel_url: cancelUrl,
      metadata: { userId: String(user?.id || ''), credits: String(credits), ...metadata },
      allow_promotion_codes: true,
      billing_address_collection: 'auto',
      ...(mode === 'subscription'
        ? { subscription_data: { metadata: { userId: String(user?.id || '') } } }
        : {}),
    };
    if (this.enabled) {
      const session = await this.client.checkout.sessions.create(params);
      return { id: session.id, url: session.url, customerId };
    }
    return {
      id: `cs_mock_${Date.now()}`,
      url: `${process.env.FRONTEND_URL || 'http://localhost:5173'}/mock-checkout?session=cs_mock_${Date.now()}`,
      customerId,
      mock: true,
    };
  }

  async createPortalSession({ user, returnUrl }) {
    if (!this.enabled) {
      return { url: returnUrl || `${process.env.FRONTEND_URL || 'http://localhost:5173'}/billing` };
    }
    if (!user?.stripeCustomerId) {
      throw new Error('Customer not created yet');
    }
    const session = await this.client.billingPortal.sessions.create({
      customer: user.stripeCustomerId,
      return_url: returnUrl || `${process.env.FRONTEND_URL || 'http://localhost:5173'}/billing`,
    });
    return { url: session.url };
  }

  async verifyPaymentIntent(paymentIntentId) {
    if (!this.enabled) {
      return { status: 'succeeded', succeeded: true, mock: true };
    }
    const pi = await this.client.paymentIntents.retrieve(paymentIntentId);
    return { status: pi.status, succeeded: pi.status === 'succeeded', mock: false };
  }

  async cancelSubscription(stripeSubscriptionId) {
    if (!this.enabled) return { success: true, mock: true };
    const sub = await this.client.subscriptions.cancel(stripeSubscriptionId);
    return { success: true, status: sub.status };
  }
}

export default new StripeService();