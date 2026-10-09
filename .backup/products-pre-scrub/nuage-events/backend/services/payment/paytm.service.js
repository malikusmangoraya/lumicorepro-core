import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

class PaytmService {
  constructor() {
    const config = getGatewayConfig('paytm');
    this.enabled = config?.enabled || false;
    this.merchantId = process.env.PAYTM_MERCHANT_ID;
    this.merchantKey = process.env.PAYTM_MERCHANT_KEY;
    this.website = process.env.PAYTM_WEBSITE || 'WEBSTAGING';
    this.industryType = process.env.PAYTM_INDUSTRY_TYPE || 'Retail';
    this.channelId = process.env.PAYTM_CHANNEL_ID || 'WEB';
    this.mode = process.env.PAYTM_MODE || 'sandbox';
    this.baseURL =
      this.mode === 'sandbox' ? 'https://securegw-stage.paytm.in' : 'https://securegw.paytm.in';
    this.name = 'Paytm';
    this.description = 'Digital wallet & UPI (India)';
    this.supportedCurrencies = ['inr'];
    this.region = 'India';
    this.icon = '📱';
  }

  _generateChecksum(params) {
    const sortedKeys = Object.keys(params).sort();
    const str = sortedKeys
      .map((k) => (params[k] ? `${k}=${params[k]}` : ''))
      .filter(Boolean)
      .join('&|');
    return str + '|key=' + this.merchantKey;
  }

  _encrypt(data, salt) {
    const hasher = crypto.createHash('sha256').update(this._generateChecksum(data) + salt);
    const key = crypto.createHmac('sha256', salt).update(hasher.digest('hex')).digest();
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
    const encrypted = Buffer.concat([cipher.update(JSON.stringify(data), 'utf8'), cipher.final()]);
    return Buffer.concat([iv, encrypted]).toString('base64');
  }

  _decrypt(data) {
    // For server-to-server verification
    const decoded = Buffer.from(data, 'base64');
    const iv = decoded.slice(0, 16);
    const encrypted = decoded.slice(16);
    return { iv, encrypted };
  }

  async initiateTransaction({ amount, orderId, email, phone, callbackUrl }) {
    if (!this.enabled) {
      return {
        txnId: `paytm_mock_${Date.now()}`,
        redirectURL: '#paytm_mock',
        mock: true,
      };
    }

    const txnToken = `TXN_${Date.now()}`;
    const params = {
      MERCHANT_ID: this.merchantId,
      CHANNEL_ID: this.channelId,
      INDUSTRY_TYPE_ID: this.industryType,
      WEBSITE: this.website,
      ORDER_ID: orderId,
      TXN_AMOUNT: amount.toFixed(2),
      CURRENCY: 'INR',
      CALLBACK_URL: callbackUrl,
      EMAIL: email,
      MOBILE_NO: phone,
      TXN_TOKEN: txnToken,
    };

    const checksum = crypto
      .createHash('sha256')
      .update(this._generateChecksum(params))
      .digest('hex');

    // For staging, typically use Paytm's transaction token endpoint
    return {
      txnToken,
      redirectURL: `${this.baseURL}/theia/processTransaction`,
      params,
      checksum,
      mock: false,
    };
  }

  async verifyChecksum(params, checksum) {
    // Verify response checksum from Paytm
    const sortedKeys = Object.keys(params)
      .filter((k) => k !== 'CHECKSUMHASH')
      .sort();
    const str = sortedKeys
      .map((k) => (params[k] ? `${k}=${params[k]}` : ''))
      .filter(Boolean)
      .join('&|');
    const generatedChecksum = crypto
      .createHash('sha256')
      .update(str + '|key=' + this.merchantKey)
      .digest('hex');
    return generatedChecksum === checksum;
  }

  async refund({ orderId, txnAmount, refundId }) {
    if (!this.enabled) return { success: true, mock: true, orderId, refundId };

    const body = {
      MERCHANT_ID: this.merchantId,
      ORDER_ID: orderId,
      TXN_AMOUNT: txnAmount.toString(),
      REFUND_ID: refundId,
      EMAIL: 'refund@merchant.com',
      MOBILE_NO: '0000000000',
    };

    const checksum = crypto.createHash('sha256').update(this._generateChecksum(body)).digest('hex');

    const res = await fetch(`${this.baseURL}/theia/logInnerActivity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, CHECKSUMHASH: checksum, REQUEST_TYPE: 'REFUND' }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Paytm refund failed: ${text}`);
    }

    const data = await res.json();
    return { success: data?.STATUS === 'TXN_SUCCESS', orderId, refundId };
  }
}

export default new PaytmService();
