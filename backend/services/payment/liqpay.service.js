import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

/**
 * LiqPay (Ukraine/CIS). Signing rules per LiqPay API v3:
 *   signature = base64( sha1( private_key + data + private_key ) )
 * where `data` is the BASE64-ENCODED JSON payload (not the decoded JSON).
 * The previous implementation signed the decoded JSON with SHA-256, so every
 * genuine callback was rejected and checkouts carried an invalid signature.
 */
class LiqPayService {
  constructor() {
    const config = getGatewayConfig('liqpay');
    this.enabled = config?.enabled || false;
    this.publicKey = process.env.LIQPAY_PUBLIC_KEY;
    this.privateKey = process.env.LIQPAY_PRIVATE_KEY;
    this.baseURL = 'https://www.liqpay.ua/api/3';
    this.checkoutURL = 'https://www.liqpay.ua/api/3/checkout';
    this.name = 'LiqPay';
    this.description = 'Ukrainian & CIS payments (Ukraine/Eastern Europe)';
    this.supportedCurrencies = ['uah', 'usd', 'eur'];
    this.region = 'Ukraine/Eastern Europe';
    this.icon = '🇺🇦';
  }

  /** @param {string} dataB64 - base64-encoded JSON payload */
  _signData(dataB64) {
    return crypto
      .createHash('sha1')
      .update(this.privateKey + dataB64 + this.privateKey)
      .digest('base64');
  }

  _safeEqual(a = '', b = '') {
    const bufA = Buffer.from(String(a));
    const bufB = Buffer.from(String(b));
    if (bufA.length !== bufB.length) return false;
    return crypto.timingSafeEqual(bufA, bufB);
  }

  async createPaymentForm({ amount, currency, orderId, description, productName, serverUrl }) {
    if (!this.enabled) {
      return {
        publicKey: 'gcb_public_key',
        action: this.checkoutURL,
        data: '',
        sign: '',
        mock: true,
      };
    }

    const payload = JSON.stringify({
      version: '3',
      public_key: this.publicKey,
      action: 'pay',
      amount,
      currency_code: currency || 'UAH',
      order_id: orderId,
      description: description,
      product_name: productName,
      server_url: serverUrl,
    });

    const dataB64 = Buffer.from(payload).toString('base64');
    const sign = this._signData(dataB64);

    return {
      publicKey: this.publicKey,
      action: this.checkoutURL,
      data: dataB64,
      sign,
      mock: false,
    };
  }

  async handleCallback(event) {
    if (!event?.data || !event?.sign) {
      return { error: 'Missing data or signature' };
    }

    // Signature is computed over the base64 `data` string as received.
    if (!this._safeEqual(event.sign, this._signData(event.data))) {
      logger.warn('LiqPay callback signature mismatch');
      return { error: 'Invalid signature' };
    }

    let decoded;
    try {
      decoded = JSON.parse(Buffer.from(event.data, 'base64').toString('utf8'));
    } catch {
      return { error: 'Invalid payload' };
    }

    logger.info(`LiqPay callback: order=${decoded.order_id}, status=${decoded.status}`);
    return decoded;
  }

  async refund({ orderId, amount, currency }) {
    const action = JSON.stringify({
      version: '3',
      public_key: this.publicKey,
      action: 'refund',
      order_id: orderId,
      amount,
      currency_code: currency || 'UAH',
    });
    const dataB64 = Buffer.from(action).toString('base64');
    const sign = this._signData(dataB64);

    if (!this.enabled) {
      return { sign, mock: true };
    }

    // Server API endpoint is /api/3/request (previously hit /api/3//checkout).
    const res = await fetch(`${this.baseURL}/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `data=${encodeURIComponent(dataB64)}&sign=${encodeURIComponent(sign)}`,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`LiqPay refund failed: ${text}`);
    }

    const data = await res.text();
    return JSON.parse(data);
  }

  getPublicKey() {
    return process.env.LIQPAY_PUBLIC_KEY || 'gcb_your_public_key';
  }
}

export default new LiqPayService();
