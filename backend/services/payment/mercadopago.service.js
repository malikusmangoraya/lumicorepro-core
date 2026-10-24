import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class MercadoPagoService {
  constructor() {
    const config = getGatewayConfig('mercadopago');
    this.enabled = config?.enabled || false;
    this.accessToken = process.env.MERCADOPAGO_ACCESS_TOKEN;
    this.publicKey = process.env.MERCADOPAGO_PUBLIC_KEY;
    this.webhookSecret =
      config?.webhookPassword || process.env.MERCADOPAGO_WEBHOOK_SECRET || '';
    this.baseURL = 'https://api.mercadopago.com';
    this.name = 'Mercado Pago';
    this.description = 'Latin American payments & checkout (Latin America)';
    this.supportedCurrencies = ['ars', 'brl', 'clp', 'cop', 'mxn', 'pen', 'pyg', 'uy', 'usd', 'eur', 'gbp'];
    this.region = 'Latin America';
    this.icon = '💲';
  }

  async createPreference({ items, paymentMethods, backUrl }) {
    if (!this.enabled) {
      const prefId = `mp_mock_${Date.now()}`;
      return { id: prefId, init_point: '#', mock: true };
    }

    const res = await fetch(`${this.baseURL}/v1/preferences`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify({
        items: items || [],
        back_url: backUrl,
        auto_return: 'approved',
        payment_methods: paymentMethods,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Mercado Pago preference failed: ${text}`);
    }

    const data = await res.json();
    return { ...data, mock: false };
  }

  async processPayment({ amount, description, payerEmail, token, installments = 1 }) {
    if (!this.enabled) {
      const paymentId = `mpayment_mock_${Date.now()}`;
      return { id: paymentId, status: 'approved', mock: true };
    }

    const res = await fetch(`${this.baseURL}/v1/payments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify({
        transaction_amount: amount,
        description,
        payment_method_id: 'visa',
        payer: { email: payerEmail },
        token,
        installments,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Mercado Pago payment failed: ${text}`);
    }

    const data = await res.json();
    return { ...data, mock: false };
  }

  async refund({ paymentId, amount }) {
    if (!this.enabled) return { success: true, mock: true, paymentId };

    const body = amount > 0 ? { amount } : undefined;
    const res = await fetch(`${this.baseURL}/v1/payments/${paymentId}/refunds`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Mercado Pago refund failed: ${text}`);
    }

    const data = await res.json();
    return { success: true, refunds: data };
  }

  /**
   * Verify Mercado Pago's `x-signature` header.
   * Header format: `ts=<ts>,v1=<hmacSha256Hex>`; manifest is
   * `id:<data.id>;request-id:<x-request-id>;ts:<ts>;` keyed by the webhook
   * secret. Rejects unsigned events (fail-closed) because the previous version
   * only logged them — a forged webhook could mark any payment as paid.
   *
   * @param {string} dataId - payment/order id from the notification URL/body
   * @param {object} headers - request headers (lowercased keys expected)
   * @returns {boolean}
   */
  verifyWebhook(dataId, headers = {}) {
    if (!this.webhookSecret) {
      logger.warn('Mercado Pago webhook rejected: webhook secret is not configured');
      return false;
    }
    const signature = headers['x-signature'] || headers['X-Signature'];
    const requestId = headers['x-request-id'] || headers['X-Request-Id'] || '';
    if (!signature || !dataId) return false;

    const parts = Object.fromEntries(
      String(signature)
        .split(',')
        .map((p) => p.split('='))
        .filter((kv) => kv.length === 2)
    );
    const ts = parts.ts;
    const v1 = parts.v1;
    if (!ts || !v1) return false;

    const manifest = `id:${dataId};request-id:${requestId};ts:${ts};`;
    const expected = crypto.createHmac('sha256', this.webhookSecret).update(manifest).digest('hex');

    const a = Buffer.from(expected);
    const b = Buffer.from(v1);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  }

  async handleWebhook(event, headers = {}) {
    const dataId = event?.data?.id || event?.id;
    if (!this.verifyWebhook(dataId, headers)) {
      return { valid: false, reason: 'invalid or missing signature' };
    }

    switch (event.action || event.type) {
      case 'payment':
        logger.info(`Mercado Pago payment event: ${dataId}`);
        break;
      case 'refund':
        logger.info(`Mercado Pago refund event: ${dataId}`);
        break;
      default:
        logger.info(`Unhandled Mercado Pago webhook: ${event.action || event.type}`);
    }
    return { valid: true };
  }

  getPublicKey() {
    return process.env.MERCADOPAGO_PUBLIC_KEY || 'TEST_PUBLIC_KEY';
  }
}

export default new MercadoPagoService();