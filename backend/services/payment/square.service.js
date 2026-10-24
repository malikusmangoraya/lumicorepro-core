import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

const ZERO_DECIMAL = new Set(['jpy']);

class SquareService {
  constructor() {
    const config = getGatewayConfig('square');
    this.enabled = config?.enabled || false;
    this.accessToken = process.env.SQUARE_ACCESS_TOKEN;
    this.locationId = process.env.SQUARE_LOCATION_ID;
    this.signatureKey = process.env.SQUARE_WEBHOOK_SIGNATURE_KEY || '';
    this.environment = process.env.SQUARE_ENVIRONMENT || 'sandbox';
    this.baseURL = this.environment === 'sandbox'
      ? 'https://connect.squareupsandbox.com'
      : 'https://connect.squareup.com';
    this.name = 'Square';
    this.description = 'Credit card & contactless payments (US, Japan, Australia)';
    this.supportedCurrencies = ['usd', 'jpy', 'aud', 'gbp', 'cad'];
    this.region = 'US/Japan/Australia';
    this.icon = '🔲';
  }

  /** Square amounts are minor units; JPY has no minor unit (×100 overcharges). */
  _toMinorUnits(amount, currency = 'usd') {
    return Math.round(ZERO_DECIMAL.has(String(currency).toLowerCase()) ? amount : amount * 100);
  }

  async createPayment({ amount, currency = 'usd', idempotencyKey, sourceId }) {
    if (!this.enabled) {
      const paymentId = `sq_mock_${Date.now()}`;
      return { id: paymentId, amount, mock: true };
    }

    // Live card charges need a Web Payments SDK token (`source_id`); without it
    // Square rejects the request — surface that clearly instead of a bare 400.
    if (!sourceId) {
      throw new Error('Square createPayment requires sourceId (Web Payments SDK token)');
    }

    const res = await fetch(`${this.baseURL}/v2/payments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
        'Idempotency-Key': idempotencyKey || `sq_${Date.now()}`,
      },
      body: JSON.stringify({
        idempotency_key: idempotencyKey || `sq_${Date.now()}`,
        source_id: sourceId,
        amount_money: {
          amount: this._toMinorUnits(amount, currency),
          currency: currency.toUpperCase(),
        },
        location_id: this.locationId,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Square create payment failed: ${text}`);
    }

    const data = await res.json();
    return { ...data.payment, mock: false };
  }

  async refund({ paymentId, amount, currency = 'usd' }) {
    if (!this.enabled) return { success: true, mock: true, paymentId };

    // Refunds are created via POST /v2/refunds with `amount_money` — the old
    // `/v2/payments/{id}/refund` + `refund_money` shape does not exist.
    const res = await fetch(`${this.baseURL}/v2/refunds`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
        'Idempotency-Key': `refund_${paymentId}_${Date.now()}`,
      },
      body: JSON.stringify({
        idempotency_key: `refund_${paymentId}_${Date.now()}`,
        payment_id: paymentId,
        amount_money: {
          amount: this._toMinorUnits(amount ?? 0, currency),
          currency: currency.toUpperCase(),
        },
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Square refund failed: ${text}`);
    }

    const data = await res.json();
    return { success: true, refundId: data.refund?.id };
  }

  /**
   * Verify Square's `x-square-hmacsha256-signature` header: base64 HMAC-SHA256
   * over `<notification URL><raw body>`, keyed by the webhook signature key.
   * Fail-closed when the key is not configured.
   */
  verifyWebhook(rawBody, signature, notificationUrl) {
    if (!this.signatureKey) {
      logger.warn('Square webhook rejected: SQUARE_WEBHOOK_SIGNATURE_KEY is not configured');
      return false;
    }
    if (!rawBody || !signature || !notificationUrl) return false;
    const expected = crypto
      .createHmac('sha256', this.signatureKey)
      .update(`${notificationUrl}${rawBody}`)
      .digest('base64');
    const a = Buffer.from(expected);
    const b = Buffer.from(String(signature));
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  }

  async handleWebhook(event, { signature, rawBody, notificationUrl } = {}) {
    if (!this.verifyWebhook(rawBody, signature, notificationUrl)) {
      return { valid: false, reason: 'invalid or missing signature' };
    }

    // Real Square payload: data.object.payment.id; event types are
    // payment.created / payment.updated (not completed/canceled).
    const paymentId = event?.data?.object?.payment?.id;
    switch (event?.type) {
      case 'payment.created':
        logger.info(`Square payment created: ${paymentId}`);
        break;
      case 'payment.updated':
        logger.info(`Square payment updated: ${paymentId}`);
        break;
      default:
        logger.info(`Unhandled Square webhook: ${event?.type}`);
    }
    return { valid: true };
  }
}

export default new SquareService();
