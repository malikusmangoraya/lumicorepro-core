import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class FlutterwaveService {
  constructor() {
    const config = getGatewayConfig('flutterwave');
    this.enabled = config?.enabled || false;
    this.publicKey = process.env.FLUTTERWAVE_PUBLIC_KEY;
    this.secretKey = process.env.FLUTTERWAVE_SECRET_KEY;
    this.encryptionKey = process.env.FLUTTERWAVE_ENCRYPTION_KEY;
    this.baseURL = 'https://api.flutterwave.com/v3';
    this.name = 'Flutterwave';
    this.description = 'African payments (Africa)';
    this.supportedCurrencies = ['ngn', 'ghs', 'ksh', 'egp', 'usd', 'gbp', 'eur', 'zar', 'tzs'];
    this.region = 'Africa';
    this.icon = '🌍';
  }

  _authHeader() {
    return `Bearer ${this.secretKey}`;
  }

  async initializeTransaction({
    amount,
    currency,
    email,
    firstName,
    lastName,
    txRef,
    redirectUrl,
    meta = {},
  }) {
    if (!this.enabled) {
      const transferId = `flw_mock_${Date.now()}`;
      return {
        id: transferId,
        link: redirectUrl || '#',
        status: 'success',
        mock: true,
      };
    }

    const res = await fetch(`${this.baseURL}/payments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: this._authHeader(),
      },
      body: JSON.stringify({
        amount,
        currency,
        email,
        first_name: firstName,
        last_name: lastName,
        tx_ref: txRef,
        redirect_url: redirectUrl,
        meta,
        payment_options: 'card,banktransfer,ussd',
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Flutterwave initialize failed: ${text}`);
    }

    const data = await res.json();
    return { ...data.data, mock: false };
  }

  async verifyTransaction({ txRef, transactionId }) {
    if (!this.enabled) return { status: 'success', chargecode: '00', mock: true };

    const url = transactionId
      ? `${this.baseURL}/transactions/${transactionId}/verify`
      : `${this.baseURL}/transactions/verify?reference=${txRef}`;

    const res = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: this._authHeader(),
      },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Flutterwave verify failed: ${text}`);
    }

    const data = await res.json();
    return { ...data.data, mock: false };
  }

  async refund({ transactionId, amount }) {
    if (!this.enabled) return { id: `flw_ref_mock_${Date.now()}`, mock: true };

    const res = await fetch(`${this.baseURL}/refunds`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: this._authHeader(),
      },
      body: JSON.stringify({
        narration: 'Customer requested refund',
        id: transactionId,
        amount: amount,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Flutterwave refund failed: ${text}`);
    }

    const data = await res.json();
    return { ...data.data, mock: false };
  }

  async handleWebhook(event) {
    // Verify signature
    if (this.encryptionKey) {
      const hash = crypto
        .createHmac('sha256', this.encryptionKey)
        .update(JSON.stringify(event))
        .digest('hex');
      const sig = event[' مصنوعات_parameter_webhook_signature'];
      if (sig && sig !== hash) {
        logger.warn('Flutterwave webhook signature mismatch');
        return;
      }
    }

    switch (event.event) {
      case 'charge.success':
        logger.info(`Flutterwave charge success: ${event.data?.id}`);
        break;
      case 'charge.failed':
        logger.info(`Flutterwave charge failed: ${event.data?.id}`);
        break;
      default:
        logger.info(`Unhandled Flutterwave webhook: ${event.event}`);
    }
  }

  getPublicKey() {
    return process.env.FLUTTERWAVE_PUBLIC_KEY || 'FLWPUBK_TEST';
  }
}

export default new FlutterwaveService();
