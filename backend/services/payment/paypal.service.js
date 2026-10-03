import { getGatewayConfig } from './config.js';
import { getGatewayRuntimeConfig } from './dynamic.js';
import Order from '../../models/Order.js';
import Payment from '../../models/Payment.js';
import Notification from '../../models/Notification.js';
import { sequelize } from '../../config/database.js';
import logger from '../../utils/logger.js';

class PayPalService {
  constructor() {
    const config = getGatewayConfig('paypal');
    this.enabled = config?.enabled || false;
    this.clientId = config?.clientId;
    this.clientSecret = config?.clientSecret;
    this.mode = config?.mode || 'sandbox';
    this.baseURL = this.mode === 'sandbox'
      ? 'https://api-m.sandbox.paypal.com'
      : 'https://api-m.paypal.com';
    this.name = 'PayPal';
    this.description = 'PayPal payments (Global)';
    this.supportedCurrencies = ['usd', 'eur', 'gbp', 'cad', 'aud', 'jpy', 'sek', 'chf'];
    this.region = 'Global';
    this.icon = '🅿️';
  }

  /**
   * Re-initialize credentials from runtime SystemConfig (called after the admin
   * saves new keys). Keeps the singleton in sync without a restart.
   */
  async refresh() {
    const cfg = await getGatewayRuntimeConfig('paypal');
    this.clientId = cfg.clientId;
    this.clientSecret = cfg.clientSecret;
    this.mode = cfg.mode || 'sandbox';
    this.baseURL = this.mode === 'sandbox'
      ? 'https://api-m.sandbox.paypal.com'
      : 'https://api-m.paypal.com';
    this.enabled = !!cfg.enabled;
    return { enabled: this.enabled };
  }

  async getAccessToken() {
    const auth = Buffer.from(`${this.clientId}:${this.clientSecret}`).toString('base64');
    const res = await fetch(`${this.baseURL}/v1/oauth2/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Authorization: `Basic ${auth}`,
      },
      body: 'grant_type=client_credentials',
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal auth failed: ${text}`);
    }
    const data = await res.json();
    return data.access_token;
  }

  /**
   * Resolve the PayPal webhook id: runtime SystemConfig (DB → Redis) first,
   * then PAYPAL_WEBHOOK_ID. Empty string means webhooks cannot be verified.
   *
   * @returns {Promise<string>} webhook id, or '' when unconfigured
   */
  async getWebhookId() {
    const cfg = await getGatewayRuntimeConfig('paypal').catch(() => null);
    return cfg?.webhookId || process.env.PAYPAL_WEBHOOK_ID || '';
  }

  /**
   * Verify a webhook delivery with PayPal's verification API.
   *
   * PayPal signs deliveries with a rotating certificate, so the only sound
   * check is to send the `paypal-transmission-*` headers back to
   * POST /v1/notifications/verify-webhook-signature and require an explicit
   * `verification_status === 'SUCCESS'`. Anything else (including a missing
   * header) is treated as unverified.
   *
   * @param {object} params - Verification inputs
   * @param {string} params.transmissionId - `paypal-transmission-id` header
   * @param {string} params.transmissionTime - `paypal-transmission-time` header
   * @param {string} params.transmissionSig - `paypal-transmission-sig` header
   * @param {string} params.certUrl - `paypal-cert-url` header
   * @param {string} params.authAlgo - `paypal-auth-algo` header
   * @param {string} params.webhookId - PAYPAL_WEBHOOK_ID (or SystemConfig)
   * @param {object} params.webhookEvent - Parsed webhook body
   * @returns {Promise<boolean>} true only on an explicit PayPal SUCCESS
   */
  async verifyWebhookSignature({
    transmissionId,
    transmissionTime,
    transmissionSig,
    certUrl,
    authAlgo,
    webhookId,
    webhookEvent,
  }) {
    const hasAllHeaders =
      transmissionId && transmissionTime && transmissionSig && certUrl && authAlgo;
    if (!webhookId || !hasAllHeaders) {
      return false;
    }

    const token = await this.getAccessToken();
    const res = await fetch(`${this.baseURL}/v1/notifications/verify-webhook-signature`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        transmission_id: transmissionId,
        transmission_time: transmissionTime,
        transmission_sig: transmissionSig,
        cert_url: certUrl,
        auth_algo: authAlgo,
        webhook_id: webhookId,
        webhook_event: webhookEvent,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal webhook verification request failed: ${text}`);
    }

    const data = await res.json();
    return data?.verification_status === 'SUCCESS';
  }

  async createOrder({ amount, currency = 'usd', orderId, description }) {
    if (!this.enabled) {
      const orderId_ = `paypal_mock_${Date.now()}`;
      return { id: orderId_, amount, currency, mock: true, approvalUrl: '#' };
    }

    const token = await this.getAccessToken();
    const res = await fetch(`${this.baseURL}/v2/checkout/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        intent: 'CAPTURE',
        purchase_units: [{
          reference_id: orderId?.toString(),
          description,
          amount: {
            currency_code: currency.toUpperCase(),
            value: amount.toFixed(2),
          },
        }],
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal create order failed: ${text}`);
    }

    const data = await res.json();
    const approvalUrl = data.links?.find(l => l.rel === 'approve')?.href;
    return {
      id: data.id,
      approvalUrl,
      amount,
      currency,
      mock: false,
    };
  }

  async captureOrder({ orderId }) {
    if (!this.enabled) return { success: true, mock: true, orderId };

    const token = await this.getAccessToken();
    const res = await fetch(`${this.baseURL}/v2/checkout/orders/${orderId}/capture`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal capture failed: ${text}`);
    }

    const data = await res.json();
    return {
      success: data.status === 'COMPLETED',
      captureId: data.purchase_units?.[0]?.payments?.captures?.[0]?.id,
      status: data.status,
    };
  }

  async refund({ paymentId, amount }) {
    if (!this.enabled) return { success: true, mock: true, paymentId };

    const token = await this.getAccessToken();
    const body = amount ? { amount: { currency_code: 'USD', value: amount.toFixed(2) } } : undefined;
    const res = await fetch(`${this.baseURL}/v2/payments/captures/${paymentId}/refund`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal refund failed: ${text}`);
    }

    const data = await res.json();
    return { success: true, refundId: data.id };
  }

  /**
   * Fulfil a `PAYMENT.CAPTURE.COMPLETED` event: mark the matching Payment as
   * succeeded and flip its Order to paid inside a single transaction. Mirrors
   * the Stripe webhook fulfilment in routes/payment.routes.js.
   *
   * Never throws for an unmatched capture/order — a webhook that cannot be
   * fulfilled still returns 200 so PayPal stops retrying, and the durable
   * webhook_events ledger records the delivery.
   *
   * @param {object} capture - event.resource from the capture event
   * @returns {Promise<{handled: boolean, orderId: number|null, duplicate?: boolean}>}
   */
  async _fulfilCapture(capture) {
    const captureId = capture?.id || null;
    const paypalOrderId = capture?.supplementary_data?.related_ids?.order_id || null;

    if (!captureId && !paypalOrderId) {
      logger.warn(
        'PayPal webhook: capture event carries no capture/order id — acknowledged without change',
      );
      return { handled: false, orderId: null };
    }

    return sequelize.transaction(async (t) => {
      const payment = (captureId
        ? await Payment.findOne({
          where: { provider: 'paypal', stripeChargeId: captureId },
          transaction: t,
        })
        : null)
        || (paypalOrderId
          ? await Payment.findOne({
            where: { provider: 'paypal', stripePaymentIntentId: paypalOrderId },
            transaction: t,
          })
          : null);

      if (!payment) {
        logger.warn(
          `PayPal webhook: no payment matches capture ${captureId || '(none)'} / order ` +
            `${paypalOrderId || '(none)'} — acknowledged without change`,
        );
        return { handled: false, orderId: null };
      }

      await payment.update({
        status: 'succeeded',
        stripeChargeId: captureId || payment.stripeChargeId,
        providerResponse: {
          paypalOrderId,
          captureId,
          status: capture?.status || 'COMPLETED',
          verifiedVia: 'webhook',
        },
      }, { transaction: t });

      if (!payment.order_id) {
        logger.warn(`PayPal webhook: payment ${payment.id} has no order to fulfil`);
        return { handled: true, orderId: null };
      }

      const order = await Order.findByPk(payment.order_id, { transaction: t });
      if (!order) {
        logger.warn(`PayPal webhook: order ${payment.order_id} not found — acknowledged without change`);
        return { handled: true, orderId: null };
      }

      if (order.isPaid) {
        logger.info(`PayPal webhook: order ${order.id} already paid — duplicate delivery ignored`);
        return { handled: true, orderId: order.id, duplicate: true };
      }

      await order.update({
        isPaid: true,
        paidAt: new Date(),
        status: 'processing',
        paymentResult: {
          id: paypalOrderId || captureId,
          captureId,
          status: 'succeeded',
          provider: 'paypal',
          updateTime: new Date().toISOString(),
          emailAddress: capture?.payer?.email_address || null,
        },
      }, { transaction: t });

      // `recipient` is NOT NULL — only notify when the order is user-bound.
      if (order.user_id != null) {
        await Notification.create({
          recipient: order.user_id,
          type: 'payment',
          title: 'PayPal Payment Successful',
          message: `PayPal payment of $${Number(order.totalPrice || 0).toFixed(2)} for order #${order.orderNumber} received.`,
          link: '/templates/ecommerce/OrdersHistory',
          metadata: {},
        }, { transaction: t });
      }

      logger.info(`PayPal webhook: order ${order.id} marked paid (capture ${captureId || 'n/a'})`);
      return { handled: true, orderId: order.id };
    });
  }

  /**
   * Handle a verified PayPal webhook event.
   *
   * Only `PAYMENT.CAPTURE.COMPLETED` mutates state (order/payment → paid); every
   * other event type is logged and acknowledged.
   *
   * @param {object} event - Verified PayPal webhook body
   * @returns {Promise<{handled: boolean, orderId: number|null, duplicate?: boolean}>}
   */
  async handleWebhook(event) {
    switch (event.event_type) {
      case 'PAYMENT.CAPTURE.COMPLETED': {
        return this._fulfilCapture(event.resource || {});
      }
      case 'PAYMENT.CAPTURE.DENIED': {
        logger.info(`PayPal capture denied: ${event.resource?.id}`);
        return { handled: false, orderId: null };
      }
      default:
        logger.info(`Unhandled PayPal webhook: ${event.event_type}`);
        return { handled: false, orderId: null };
    }
  }
}

export default new PayPalService();
