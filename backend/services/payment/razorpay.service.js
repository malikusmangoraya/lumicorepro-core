import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class RazorpayService {
  constructor() {
    const config = getGatewayConfig('razorpay');
    this.enabled = config?.enabled || false;
    this.keyId = process.env.RAZORPAY_KEY_ID;
    this.keySecret = process.env.RAZORPAY_KEY_SECRET;
    this.baseURL = 'https://api.razorpay.com';
    this.name = 'Razorpay';
    this.description = 'Indian payment gateway (India)';
    this.supportedCurrencies = ['inr'];
    this.region = 'India';
    this.icon = '🇮🇳';
  }

  _authHeader() {
    return Buffer.from(`${this.keyId}:${this.keySecret}`).toString('base64');
  }

  async createOrder({ amount, currency = 'INR', receipt, notes = {} }) {
    if (!this.enabled) {
      const orderId = `rzp_mock_${Date.now()}`;
      return { id: orderId, amount: Math.round(amount * 100), currency, mock: true };
    }

    const res = await fetch(`${this.baseURL}/v1/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Basic ${this._authHeader()}`,
      },
      body: JSON.stringify({
        amount: Math.round(amount * 100),
        currency,
        receipt,
        notes,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Razorpay create order failed: ${text}`);
    }

    const data = await res.json();
    return { ...data, mock: false };
  }

  async verifyPayment({ orderId, paymentId, signature }) {
    const sign = `${orderId}|${paymentId}`;
    const expected = crypto.createHmac('sha256', this.keySecret)
      .update(sign.toString())
      .digest('hex');
    const a = Buffer.from(expected);
    const b = Buffer.from(String(signature || ''));
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  }

  async refund({ paymentId, amount }) {
    if (!this.enabled) {
      return { success: true, mock: true, refundId: `ref_mock_${Date.now()}` };
    }

    const body = {
      payment_id: paymentId,
      amount: amount ? Math.round(amount * 100) : undefined,
    };
    const res = await fetch(`${this.baseURL}/v1/payments/${paymentId}/refund`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Basic ${this._authHeader()}`,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Razorpay refund failed: ${text}`);
    }

    const data = await res.json();
    return { success: true, refundId: data.id };
  }

  /**
   * Verify a Razorpay webhook with the dashboard webhook secret.
   * Razorpay signs the RAW body with HMAC-SHA256, sent in `x-razorpay-signature`.
   * The previous handler skipped verification entirely — a forged webhook could
   * report any payment as captured.
   *
   * @param {string} rawBody - raw request body string (before JSON.parse)
   * @param {string} signature - x-razorpay-signature header
   * @returns {boolean}
   */
  verifyWebhook(rawBody, signature) {
    const secret = process.env.RAZORPAY_WEBHOOK_SECRET || '';
    if (!secret) {
      logger.warn('Razorpay webhook rejected: RAZORPAY_WEBHOOK_SECRET is not configured');
      return false;
    }
    if (!rawBody || !signature) return false;
    const expected = crypto.createHmac('sha256', secret).update(String(rawBody)).digest('hex');
    const a = Buffer.from(expected);
    const b = Buffer.from(String(signature));
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  }

  /**
   * @param {object} event - parsed webhook payload
   * @param {string} signature - x-razorpay-signature header
   * @param {string} rawBody - raw request body
   * @returns {{valid: boolean}}
   */
  async handleWebhook(event, signature, rawBody) {
    if (!this.verifyWebhook(rawBody, signature)) {
      logger.warn('Razorpay webhook signature mismatch');
      return { valid: false };
    }
    switch (event?.event) {
      case 'payment.captured': {
        logger.info(`Razorpay payment captured: ${event.payload?.payment?.entity?.id}`);
        break;
      }
      case 'payment.failed': {
        logger.info(`Razorpay payment failed: ${event.payload?.payment?.entity?.id}`);
        break;
      }
      default:
        logger.info(`Unhandled Razorpay webhook: ${event?.event}`);
    }
    return { valid: true };
  }

  getKeyId() {
    return process.env.RAZORPAY_KEY_ID || 'rzp_test_placeholder';
  }
}

export default new RazorpayService();