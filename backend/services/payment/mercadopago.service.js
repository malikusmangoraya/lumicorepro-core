import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class MercadoPagoService {
  constructor() {
    const config = getGatewayConfig('mercadopago');
    this.enabled = config?.enabled || false;
    this.accessToken = process.env.MERCADOPAGO_ACCESS_TOKEN;
    this.publicKey = process.env.MERCADOPAGO_PUBLIC_KEY;
    this.baseURL = 'https://api.mercadopago.com';
    this.name = 'Mercado Pago';
    this.description = 'Latin American payments & checkout (Latin America)';
    this.supportedCurrencies = ['ars', 'brl', 'clp', 'cop', 'mxn', 'pen', 'pym', 'uy', 'usd', 'eur', 'gbp'];
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

  async handleWebhook(event) {
    switch (event.action) {
      case 'payment':
        logger.info(`Mercado Pago payment event: ${event.data.id}`);
        break;
      case 'refund':
        logger.info(`Mercado Pago refund event: ${event.data.id}`);
        break;
      default:
        logger.info(`Unhandled Mercado Pago webhook: ${event.action}`);
    }
  }

  getPublicKey() {
    return process.env.MERCADOPAGO_PUBLIC_KEY || 'TEST_PUBLIC_KEY';
  }
}

export default new MercadoPagoService();