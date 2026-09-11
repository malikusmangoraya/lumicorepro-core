import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class LiqPayService {
  constructor() {
    const config = getGatewayConfig('liqpay');
    this.enabled = config?.enabled || false;
    this.publicKey = process.env.LIQPAY_PUBLIC_KEY;
    this.privateKey = process.env.LIQPAY_PRIVATE_KEY;
    this.baseURL = 'https://www.liqpay.ua/api/3/';
    this.name = 'LiqPay';
    this.description = 'Ukrainian & CIS payments (Ukraine/Eastern Europe)';
    this.supportedCurrencies = ['uah', 'usd', 'eur'];
    this.region = 'Ukraine/Eastern Europe';
    this.icon = '🇺🇦';
  }

  _signData(data) {
    const sign = crypto
      .createHash('sha256')
      .update(this.privateKey + data + this.privateKey)
      .digest('base64');
    return sign;
  }

  async createPaymentForm({ amount, currency, orderId, description, productName, serverUrl }) {
    if (!this.enabled) {
      return {
        publicKey: 'gcb_public_key',
        action: 'https://www.liqpay.ua/api/3/checkout',
        data: '',
        sign: '',
        mock: true,
      };
    }

    const data = JSON.stringify({
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

    const sign = this._signData(data);

    return {
      publicKey: this.publicKey,
      action: 'https://www.liqpay.ua/api/3/checkout',
      data: Buffer.from(data).toString('base64'),
      sign,
      mock: false,
    };
  }

  async handleCallback(event) {
    // Verify callback signature
    const data = Buffer.from(event.data, 'base64').toString('utf8');
    const decoded = JSON.parse(data);

    const receivedSign = event.sign;
    const expectedSign = this._signData(data);

    if (receivedSign !== expectedSign) {
      logger.warn('LiqPay callback signature mismatch');
      return { error: 'Invalid signature' };
    }

    logger.info(`LiqPay callback: order=${decoded.order_id}, status=${decoded.status}`);
    return decoded;
  }

  async refund({ orderId, amount, currency }) {
    if (!this.enabled) {
      const action = JSON.stringify({
        version: '3',
        public_key: this.publicKey,
        action: 'refund',
        order_id: orderId,
        amount,
        currency_code: currency || 'UAH',
      });
      return { sign: this._signData(action), mock: true };
    }

    const action = JSON.stringify({
      version: '3',
      public_key: this.publicKey,
      action: 'refund',
      order_id: orderId,
      amount,
      currency_code: currency || 'UAH',
    });

    const sign = this._signData(action);

    const res = await fetch(`${this.baseURL}/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `data=${Buffer.from(action).toString('base64')}&sign=${sign}`,
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