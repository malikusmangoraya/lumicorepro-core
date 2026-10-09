import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class SquareService {
  constructor() {
    const config = getGatewayConfig('square');
    this.enabled = config?.enabled || false;
    this.accessToken = process.env.SQUARE_ACCESS_TOKEN;
    this.locationId = process.env.SQUARE_LOCATION_ID;
    this.environment = process.env.SQUARE_ENVIRONMENT || 'sandbox';
    this.baseURL =
      this.environment === 'sandbox'
        ? 'https://connect.squareupsandbox.com'
        : 'https://connect.squareup.com';
    this.name = 'Square';
    this.description = 'Credit card & contactless payments (US, Japan, Australia)';
    this.supportedCurrencies = ['usd', 'jpy', 'aud', 'gbp', 'cad'];
    this.region = 'US/Japan/Australia';
    this.icon = '🔲';
  }

  async createPayment({ amount, idempotencyKey }) {
    if (!this.enabled) {
      const paymentId = `sq_mock_${Date.now()}`;
      return { id: paymentId, amount, mock: true };
    }

    const res = await fetch(`${this.baseURL}/v2/payments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
        'Idempotency-Key': idempotencyKey || `sq_${Date.now()}`,
      },
      body: JSON.stringify({
        idempotency_key: idempotencyKey || `sq_${Date.now()}`,
        amount_money: {
          amount: Math.round(amount * 100),
          currency: 'USD',
        },
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Square create payment failed: ${text}`);
    }

    const data = await res.json();
    return { ...data.payment, mock: false };
  }

  async refund({ paymentId, amount }) {
    if (!this.enabled) return { success: true, mock: true, paymentId };

    const res = await fetch(`${this.baseURL}/v2/payments/${paymentId}/refund`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
        'Idempotency-Key': `refund_${Date.now()}`,
      },
      body: JSON.stringify({
        idempotency_key: `refund_${Date.now()}`,
        refund_money: {
          amount: amount ? Math.round(amount * 100) : undefined,
          currency: 'USD',
        },
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Square refund failed: ${text}`);
    }

    const data = await res.json();
    return { success: true, refundId: data.refund?.id };
  }

  async handleWebhook(event) {
    switch (event.type) {
      case 'payment.completed':
        logger.info(`Square payment completed: ${event.data.object.id}`);
        break;
      case 'payment.canceled':
        logger.info(`Square payment canceled: ${event.data.object.id}`);
        break;
      default:
        logger.info(`Unhandled Square webhook: ${event.type}`);
    }
  }
}

export default new SquareService();
