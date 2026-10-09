/**
 * Paddle Service — Merchant of Record payments (international buyers)
 * Paddle handles global sales tax / VAT / refunds, so solo builders can sell
 * to US/EU clients from anywhere (incl. Pakistan) without a local Stripe account.
 */
import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class PaddleService {
  constructor() {
    const config = getGatewayConfig('paddle');
    this.enabled = config?.enabled || false;
    this.apiKey = process.env.PADDLE_API_KEY || '';
    this.webhookSecret = process.env.PADDLE_WEBHOOK_SECRET || '';
    this.sandbox = process.env.PADDLE_ENV === 'sandbox';
    this.baseURL = this.sandbox ? 'https://sandbox-api.paddle.com' : 'https://api.paddle.com';
    this.name = 'Paddle';
    this.description = 'Paddle (Merchant of Record) — global cards & PayPal, sales tax handled';
    this.supportedCurrencies = [
      'usd',
      'eur',
      'gbp',
      'cad',
      'aud',
      'jpy',
      'sek',
      'chf',
      'nok',
      'dkk',
      'zar',
      'brl',
      'inr',
      'sgl',
      'hkd',
    ];
    this.region = 'Global';
    this.icon = '🌊';
  }

  /**
   * Create a Paddle checkout link.
   * Real mode hits the Paddle Billing API; mock mode returns an instant URL
   * so checkout flow works without live credentials.
   */
  async createCheckout({
    amount,
    currency = 'usd',
    orderId,
    description,
    customerEmail,
    successUrl,
  }) {
    if (!this.enabled) {
      const id = `paddle_mock_${Date.now()}`;
      return {
        id,
        checkoutUrl: `https://demo.paddle.com/checkout/mock/${orderId || id}`,
        amount,
        currency,
        mock: true,
      };
    }

    const body = {
      items: [
        {
          quantity: 1,
          price: {
            unit_price: {
              amount: String(Math.round(amount * 100)),
              currency_code: currency.toUpperCase(),
            },
          },
          custom_data: { orderId: orderId?.toString() || '' },
        },
      ],
      custom_data: { orderId: orderId?.toString() || '' },
      description: description || 'LumicorePro order',
    };
    if (customerEmail) body.customer_email = customerEmail;
    if (successUrl) body.success_url = successUrl;

    const res = await fetch(`${this.baseURL}/transactions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'X-Transaction-Id': `LU-${orderId || Date.now()}`,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Paddle create checkout failed: ${text}`);
    }

    const data = await res.json();
    const txn = data?.data || {};
    return {
      id: txn.id,
      checkoutUrl: txn.urls?.checkout || '',
      amount,
      currency,
      mock: false,
    };
  }

  /**
   * Verify a Paddle webhook.
   * Signature header format: `ts=<timestamp>;h1=<base64-hmac>` where the HMAC is
   * SHA-256 of `<timestamp>:<raw body>` keyed by the webhook secret.
   */
  verifyWebhook(rawBody, signatureHeader) {
    if (!this.webhookSecret) return false;
    if (!signatureHeader) return false;

    const parts = signatureHeader.split(';');
    const ts = parts.find((p) => p.startsWith('ts='))?.slice(3);
    const h1 = parts.find((p) => p.startsWith('h1='))?.slice(3);
    if (!ts || !h1) return false;

    const expected = crypto
      .createHmac('sha256', this.webhookSecret)
      .update(`${ts}:${rawBody}`)
      .digest('base64');

    const a = Buffer.from(expected);
    const b = Buffer.from(h1);
    if (a.length !== b.length) return false;
    return crypto.timingSafeEqual(a, b);
  }

  async refund({ transactionId, amount, reason }) {
    if (!this.enabled) {
      return { success: true, mock: true, transactionId };
    }
    const res = await fetch(`${this.baseURL}/payments/${transactionId}/refunds`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${this.apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: amount ? String(Math.round(amount * 100)) : undefined,
        reason: reason || undefined,
      }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Paddle refund failed: ${text}`);
    }
    const data = await res.json();
    return { success: true, refundId: data?.data?.id, transactionId };
  }

  async handleWebhook(event) {
    const type = event?.event_type || event?.type || '';
    const payload = event?.data || {};
    logger.info(`Paddle webhook: ${type} (${payload?.id || ''})`);
    return type;
  }
}

export default new PaddleService();
