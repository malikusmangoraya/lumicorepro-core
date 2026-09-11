import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class BkashService {
  constructor() {
    const config = getGatewayConfig('bkash');
    this.enabled = config?.enabled || false;
    this.appKey = process.env.BKASH_APP_KEY;
    this.appSecret = process.env.BKASH_APP_SECRET;
    this.username = process.env.BKASH_USERNAME;
    this.password = process.env.BKASH_PASSWORD;
    this.merchantId = process.env.BKASH_MERCHANT_ID;
    this.baseURL = 'https://tokenized.pay.bka.sh/v1.2.0-beta';
    this.name = 'bKash';
    this.description = 'Mobile financial service (Bangladesh)';
    this.supportedCurrencies = ['bdt'];
    this.region = 'Bangladesh';
    this.icon = '💗';
  }

  async getAccessToken() {
    if (!this.enabled) return 'mock_token';

    const res = await fetch(`${this.baseURL}/tokenization`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-App-Key': this.appKey,
        Authorization: `Basic ${Buffer.from(`${this.appKey}:${this.appSecret}`).toString('base64')}`,
      },
      body: JSON.stringify({
        mode: '0011',
        grant_type: 'client_credentials',
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`bKash token failed: ${text}`);
    }
    const data = await res.json();
    return data.access_token;
  }

  async createPayment({ amount, orderId, callbackUrl, notifyUrl }) {
    if (!this.enabled) {
      const paymentId = `bkash_mock_${Date.now()}`;
      return {
        paymentID: paymentId,
        checkoutURL: '#',
        payment_method: 'Bkash',
        trxID: `TRX_${Date.now()}`,
        mock: true,
      };
    }

    const token = await this.getAccessToken();
    const res = await fetch(`${this.baseURL}/tokenized/checkout/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-app-key': this.appKey,
        authorization: `Bearer ${token}`,
        'apikey': this.appKey,
      },
      body: JSON.stringify({
        mode: '0011',
        payerReference: '',
        callbackURL: callbackUrl,
        amount,
        currency: 'BDT',
        packageName: 'Website Payment',
        billingEdge: {
          firstName: '',
          lastName: '',
          email: '',
        },
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`bKash create payment failed: ${text}`);
    }

    const data = await res.json();
    return { ...data, mock: false };
  }

  async executePayment({ paymentId, callbackType }) {
    if (!this.enabled) return { success: true, mock: true, paymentId };

    const token = await this.getAccessToken();
    const res = await fetch(`${this.baseURL}/tokenized/checkout/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-app-key': this.appKey,
        authorization: `Bearer ${token}`,
        'apikey': this.appKey,
      },
      body: JSON.stringify({
        mode: '0011',
        paymentID: paymentId,
        callbackType,
        signature: '',
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`bKash execute payment failed: ${text}`);
    }

    const data = await res.json();
    return { success: data.paymentStatusCode === '0000', ...data, mock: false };
  }

  async refund({ paymentId, amount }) {
    if (!this.enabled) return { success: true, mock: true, paymentId };

    const token = await this.getAccessToken();
    const res = await fetch(`${this.baseURL}/credentialized/merchant/totransaction/credit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-app-key': this.appKey,
        authorization: `Bearer ${token}`,
        'apikey': this.appKey,
      },
      body: JSON.stringify({
        mode: '0011',
        paymentType: 'REFUND',
        paymentNanoId: paymentId,
        amount: amount || '',
        currency: 'BDT',
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`bKash refund failed: ${text}`);
    }

    const data = await res.json();
    return { success: data.paymentStatusCode === '0000', ...data };
  }

  async handleWebhook(event) {
    switch (event.eventType) {
      case 'PAYMENT':
        logger.info(`bKash payment: ${event.paymentID}`);
        break;
      case 'REFUND':
        logger.info(`bKash refund: ${event.paymentID}`);
        break;
      default:
        logger.info(`Unhandled bKash webhook: ${event.eventType}`);
    }
  }
}

export default new BkashService();