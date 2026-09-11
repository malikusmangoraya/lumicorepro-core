import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class MollieService {
  constructor() {
    const config = getGatewayConfig('mollie');
    this.enabled = config?.enabled || false;
    this.apiKey = process.env.MOLLIE_API_KEY;
    this.baseURL = 'https://api.mollie.com/v2';
    this.name = 'Mollie';
    this.description = 'European payments with 20+ methods (Europe)';
    this.supportedCurrencies = ['eur', 'usd', 'gbp', 'sek', 'nok', 'dkk', 'chf', 'pln', 'czk', 'huf'];
    this.region = 'Europe';
    this.icon = '🇪🇺';
  }

  async createPayment({ amount, currency, description, redirectUrl, webhookUrl, metadata = {} }) {
    if (!this.enabled) {
      const paymentId = `tr_mock_${Date.now()}`;
      return { id: paymentId, checkout_url: '#', _links: { checkout: { href: '#' } }, mock: true };
    }

    const res = await fetch(`${this.baseURL}/payments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        amount: { value: amount.toFixed(2), currency },
        description,
        redirectUrl,
        webhookUrl,
        metadata,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Mollie create payment failed: ${text}`);
    }

    const data = await res.json();
    return { ...data, mock: false };
  }

  async getPaymentStatus(paymentId) {
    if (!this.enabled) return { status: 'paid', mock: true };

    const res = await fetch(`${this.baseURL}/payments/${paymentId}`, {
      headers: { Authorization: `Bearer ${this.apiKey}` },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Mollie get payment failed: ${text}`);
    }

    return await res.json();
  }

  async refund({ paymentId, amount, description }) {
    if (!this.enabled) return { id: 're_mock_' + Date.now(), mock: true };

    const body = { description };
    if (amount) {
      body.amount = { value: amount.toFixed(2), currency: 'EUR' };
    }

    const res = await fetch(`${this.baseURL}/payments/${paymentId}/refunds`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Mollie refund failed: ${text}`);
    }

    const data = await res.json();
    return { ...data, mock: false };
  }

  async handleWebhook(event) {
    switch (event.status) {
      case 'paid':
        logger.info(`Mollie payment paid: ${event.id}`);
        break;
      case 'failed':
        logger.info(`Mollie payment failed: ${event.id}`);
        break;
      case 'refunded':
        logger.info(`Mollie payment refunded: ${event.id}`);
        break;
      default:
        logger.info(`Unhandled Mollie webhook: ${event.status}`);
    }
  }
}

export default new MollieService();