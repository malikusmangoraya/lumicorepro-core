import crypto from 'crypto';
import { getGatewayConfig } from './config.js';
import logger from '../../utils/logger.js';

/**
 * Paytm (India: wallet/UPI/cards).
 *
 * Checksum follows Paytm's official scheme (verified against the
 * `paytmchecksum` package source):
 *   paramsString = values of params sorted by key, joined with "|"
 *   hash         = sha256(paramsString + "|" + salt).hex + salt
 *   checksum     = base64( AES-128-CBC(hash, merchantKey, IV "@@@@&&&&####$$$$") )
 * The previous implementation used a made-up SHA-256 scheme and fabricated the
 * TXN_TOKEN locally, so live payments and refunds could never work.
 */
const PAYTM_IV = '@@@@&&&&####$$$$';

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
    this.baseURL = this.mode === 'sandbox'
      ? 'https://securegw-stage.paytm.in'
      : 'https://securegw.paytm.in';
    this.name = 'Paytm';
    this.description = 'Digital wallet & UPI (India)';
    this.supportedCurrencies = ['inr'];
    this.region = 'India';
    this.icon = '📱';
    if (this.enabled && this.merchantKey && Buffer.byteLength(this.merchantKey) !== 16) {
      logger.warn('Paytm merchant key should be 16 bytes — checksum will fail with this key');
    }
  }

  _paramsString(params) {
    return Object.keys(params)
      .sort()
      .map((k) => String(params[k] ?? ''))
      .join('|');
  }

  _calculateHash(paramsString, salt) {
    return crypto.createHash('sha256').update(`${paramsString}|${salt}`).digest('hex') + salt;
  }

  _encrypt(input) {
    const cipher = crypto.createCipheriv('AES-128-CBC', this.merchantKey, PAYTM_IV);
    let encrypted = cipher.update(input, 'binary', 'base64');
    encrypted += cipher.final('base64');
    return encrypted;
  }

  _decrypt(encrypted) {
    const decipher = crypto.createDecipheriv('AES-128-CBC', this.merchantKey, PAYTM_IV);
    let decrypted = decipher.update(encrypted, 'base64', 'binary');
    decrypted += decipher.final('binary');
    return decrypted;
  }

  /** @param {object|string} params - params object or pre-serialized string */
  generateChecksum(params) {
    const paramsString = typeof params === 'string' ? params : this._paramsString(params);
    const salt = crypto.randomBytes(3).toString('base64'); // 4 chars
    return this._encrypt(this._calculateHash(paramsString, salt));
  }

  /** @returns {boolean} */
  verifyChecksum(params, checksum) {
    if (!checksum || !this.merchantKey) return false;
    try {
      const paramsString = typeof params === 'string' ? params : this._paramsString(params);
      const hash = this._decrypt(checksum);
      const salt = hash.slice(-4);
      const expected = this._calculateHash(paramsString, salt);
      const a = Buffer.from(expected);
      const b = Buffer.from(hash);
      return a.length === b.length && crypto.timingSafeEqual(a, b);
    } catch {
      return false; // malformed base64 / bad padding / wrong key
    }
  }

  async initiateTransaction({ amount, orderId, email, phone, callbackUrl }) {
    if (!this.enabled) {
      return {
        txnId: `paytm_mock_${Date.now()}`,
        redirectURL: '#paytm_mock',
        mock: true,
      };
    }

    const body = {
      requestType: 'Payment',
      mid: this.merchantId,
      websiteName: this.website,
      orderId,
      txnAmount: { value: Number(amount).toFixed(2), currency: 'INR' },
      userInfo: { custId: email || phone || orderId },
      callbackUrl,
    };
    // Sign the JSON string: nested objects (txnAmount/userInfo) would otherwise
    // stringify as "[object Object]" and the amount would not be bound to the
    // signature. This matches the official SDK's JSON.stringify(body) flow.
    const signature = this.generateChecksum(JSON.stringify(body));

    const res = await fetch(
      `${this.baseURL}/theia/api/v1/initiateTransaction?mid=${encodeURIComponent(this.merchantId)}&orderId=${encodeURIComponent(orderId)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ head: { signature }, body }),
      }
    );

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Paytm initiate transaction failed: ${text}`);
    }

    const data = await res.json();
    const resultInfo = data?.body?.resultInfo || {};
    if (resultInfo.resultStatus !== 'S') {
      throw new Error(
        `Paytm initiate transaction rejected: ${resultInfo.resultCode || 'UNKNOWN'} ${resultInfo.resultMsg || ''}`.trim()
      );
    }

    return {
      txnToken: data.body.txnToken,
      redirectURL: `${this.baseURL}/theia/api/v1/showPaymentPage?mid=${encodeURIComponent(this.merchantId)}&orderId=${encodeURIComponent(orderId)}`,
      mock: false,
    };
  }

  async verifyChecksumResponse(params, checksum) {
    return this.verifyChecksum(params, checksum);
  }

  async refund({ orderId, txnAmount, refundId }) {
    if (!this.enabled) return { success: true, mock: true, orderId, refundId };

    const body = {
      mid: this.merchantId,
      txnType: 'REFUND',
      orderId,
      txnAmount: { value: Number(txnAmount).toFixed(2), currency: 'INR' },
      refId: refundId,
    };
    const signature = this.generateChecksum(JSON.stringify(body));

    // Real refund endpoint — previously posted to /theia/logInnerActivity
    // (an analytics collector), so refunds never reached Paytm.
    const res = await fetch(`${this.baseURL}/theia/api/v1/refund`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ head: { signature }, body }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Paytm refund failed: ${text}`);
    }

    const data = await res.json();
    return {
      success: data?.body?.resultInfo?.resultStatus === 'S',
      orderId,
      refundId,
    };
  }

  /** Paytm posts CHECKSUMHASH back on callback; verify before trusting it. */
  handleCallback(params) {
    const { CHECKSUMHASH: checksum, ...rest } = params || {};
    return { valid: this.verifyChecksum(rest, checksum), params: rest };
  }
}

export default new PaytmService();
