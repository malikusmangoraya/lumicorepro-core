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
    if (!this.enabled) return { status: 'pending', mock: true };

    const res = await fetch(`${this.baseURL}/payments/${paymentId}`, {
      headers: { Authorization: `Bearer ${this.apiKey}` },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Mollie get payment failed: ${text}`);
    }

    return await res.json();
  }

  async refund({ paymentId, amount, currency, description }) {
    if (!this.enabled) return { id: 're_mock_' + Date.now(), mock: true };

    const body = { description };
    if (amount) {
      // Never assume EUR: Mollie requires the refund currency to match the
      // original payment, so read it from the payment unless one is passed.
      let refundCurrency = currency;
      if (!refundCurrency) {
        const payment = await this.getPaymentStatus(paymentId);
        refundCurrency = payment?.amount?.currency;
      }
      if (!refundCurrency) {
        throw new Error('Mollie refund: unable to determine payment currency');
      }
      body.amount = { value: Number(amount).toFixed(2), currency: refundCurrency };
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

  /**
   * Mollie webhooks are NOT signed — they only carry a payment id. Trusting the
   * posted body status (or any client-supplied status) means a forged webhook
   * can mark an unpaid order as paid. Always re-fetch the authoritative status
   * from the Mollie API before acting on it.
   *
   * @param {{id?: string}|string} payload - parsed webhook body (or raw id)
   * @returns {Promise<{valid: boolean, payment?: object, reason?: string}>}
   */
  async handleWebhook(payload) {
    const paymentId = typeof payload === 'string' ? payload : payload?.id;
    if (!paymentId) {
      logger.warn('Mollie webhook rejected: missing payment id');
      return { valid: false, reason: 'missing payment id' };
    }

    const payment = await this.getPaymentStatus(paymentId);
    logger.info(`Mollie webhook: ${paymentId} authoritative status=${payment?.status}`);
    return { valid: true, payment };
  }
}

export default new MollieService();