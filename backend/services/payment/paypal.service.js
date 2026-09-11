import { getGatewayConfig } from './config.js';
import { getGatewayRuntimeConfig } from './dynamic.js';
import logger from '../../utils/logger.js';

class PayPalService {
  constructor() {
    const config = getGatewayConfig('paypal');
    this.enabled = config?.enabled || false;
    this.clientId = config?.clientId;
    this.clientSecret = config?.clientSecret;
    this.mode = config?.mode || 'sandbox';
    this.baseURL = this.mode === 'sandbox'
      ? 'https://api-m.sandbox.paypal.com'
      : 'https://api-m.paypal.com';
    this.name = 'PayPal';
    this.description = 'PayPal payments (Global)';
    this.supportedCurrencies = ['usd', 'eur', 'gbp', 'cad', 'aud', 'jpy', 'sek', 'chf'];
    this.region = 'Global';
    this.icon = '🅿️';
  }

  /**
   * Re-initialize credentials from runtime SystemConfig (called after the admin
   * saves new keys). Keeps the singleton in sync without a restart.
   */
  async refresh() {
    const cfg = await getGatewayRuntimeConfig('paypal');
    this.clientId = cfg.clientId;
    this.clientSecret = cfg.clientSecret;
    this.mode = cfg.mode || 'sandbox';
    this.baseURL = this.mode === 'sandbox'
      ? 'https://api-m.sandbox.paypal.com'
      : 'https://api-m.paypal.com';
    this.enabled = !!cfg.enabled;
    return { enabled: this.enabled };
  }

  async getAccessToken() {
    const auth = Buffer.from(`${this.clientId}:${this.clientSecret}`).toString('base64');
    const res = await fetch(`${this.baseURL}/v1/oauth2/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Authorization: `Basic ${auth}`,
      },
      body: 'grant_type=client_credentials',
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal auth failed: ${text}`);
    }
    const data = await res.json();
    return data.access_token;
  }

  async createOrder({ amount, currency = 'usd', orderId, description }) {
    if (!this.enabled) {
      const orderId_ = `paypal_mock_${Date.now()}`;
      return { id: orderId_, amount, currency, mock: true, approvalUrl: '#' };
    }

    const token = await this.getAccessToken();
    const res = await fetch(`${this.baseURL}/v2/checkout/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        intent: 'CAPTURE',
        purchase_units: [{
          reference_id: orderId?.toString(),
          description,
          amount: {
            currency_code: currency.toUpperCase(),
            value: amount.toFixed(2),
          },
        }],
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal create order failed: ${text}`);
    }

    const data = await res.json();
    const approvalUrl = data.links?.find(l => l.rel === 'approve')?.href;
    return {
      id: data.id,
      approvalUrl,
      amount,
      currency,
      mock: false,
    };
  }

  async captureOrder({ orderId }) {
    if (!this.enabled) return { success: true, mock: true, orderId };

    const token = await this.getAccessToken();
    const res = await fetch(`${this.baseURL}/v2/checkout/orders/${orderId}/capture`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal capture failed: ${text}`);
    }

    const data = await res.json();
    return {
      success: data.status === 'COMPLETED',
      captureId: data.purchase_units?.[0]?.payments?.captures?.[0]?.id,
      status: data.status,
    };
  }

  async refund({ paymentId, amount }) {
    if (!this.enabled) return { success: true, mock: true, paymentId };

    const token = await this.getAccessToken();
    const body = amount ? { amount: { currency_code: 'USD', value: amount.toFixed(2) } } : undefined;
    const res = await fetch(`${this.baseURL}/v2/payments/captures/${paymentId}/refund`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`PayPal refund failed: ${text}`);
    }

    const data = await res.json();
    return { success: true, refundId: data.id };
  }

  async handleWebhook(event) {
    switch (event.event_type) {
      case 'PAYMENT.CAPTURE.COMPLETED': {
        const capture = event.resource;
        logger.info(`PayPal capture completed: ${capture.id}`);
        break;
      }
      case 'PAYMENT.CAPTURE.DENIED': {
        logger.info(`PayPal capture denied: ${event.resource.id}`);
        break;
      }
      default:
        logger.info(`Unhandled PayPal webhook: ${event.event_type}`);
    }
  }
}

export default new PayPalService();