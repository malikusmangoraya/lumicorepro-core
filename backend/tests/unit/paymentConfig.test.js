import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

const ENV_KEYS = [
  'STRIPE_SECRET_KEY', 'STRIPE_PUBLISHABLE_KEY', 'STRIPE_WEBHOOK_SECRET',
  'PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET', 'PAYPAL_MODE', 'PAYPAL_WEBHOOK_ID',
  'RAZORPAY_KEY_ID', 'RAZORPAY_KEY_SECRET', 'SQUARE_ACCESS_TOKEN', 'SQUARE_LOCATION_ID',
  'BKASH_APP_KEY', 'MOLLIE_API_KEY', 'FLUTTERWAVE_SECRET_KEY', 'PAYTM_MERCHANT_ID',
  'MERCADOPAGO_ACCESS_TOKEN', 'LIQPAY_PUBLIC_KEY', 'PADDLE_API_KEY',
  'PAYMENT_GATEWAYS_ENABLED', 'PAYPAL_MODE',
];

let saved;
beforeEach(() => {
  saved = {};
  for (const k of ENV_KEYS) {
    saved[k] = process.env[k];
    delete process.env[k];
  }
});
afterEach(() => {
  for (const k of ENV_KEYS) {
    if (saved[k] === undefined) delete process.env[k];
    else process.env[k] = saved[k];
  }
});

const { getGatewayConfig, getEnabledGateways, isGatewayEnabled, warnLiveKeys } = await import(
  '../../services/payment/config.js'
);

describe('getGatewayConfig', () => {
  it('returns null for an unknown gateway', () => {
    expect(getGatewayConfig('bitcoin')).toBeNull();
  });

  it('marks stripe disabled when no key is set', () => {
    expect(getGatewayConfig('stripe').enabled).toBe(false);
  });

  it('marks stripe enabled with a real key', () => {
    process.env.STRIPE_SECRET_KEY = 'sk_test_abc123';
    const c = getGatewayConfig('stripe');
    expect(c.enabled).toBe(true);
    expect(c.secretKey).toBe('sk_test_abc123');
  });

  it('treats the .env.example "your_" placeholder as NOT configured', () => {
    // Shipping with the template value must never look like a live gateway.
    process.env.STRIPE_SECRET_KEY = 'your_stripe_secret_key_here';
    expect(getGatewayConfig('stripe').enabled).toBe(false);
  });

  it('defaults paypal to sandbox mode', () => {
    process.env.PAYPAL_CLIENT_ID = 'AY123';
    expect(getGatewayConfig('paypal').mode).toBe('sandbox');
  });

  it('honours an explicit paypal live mode', () => {
    process.env.PAYPAL_CLIENT_ID = 'AY123';
    process.env.PAYPAL_MODE = 'live';
    expect(getGatewayConfig('paypal').mode).toBe('live');
  });

  it('applies paytm defaults for website/industry/channel', () => {
    const c = getGatewayConfig('paytm');
    expect(c.website).toBe('WEBSTAGING');
    expect(c.industryType).toBe('Retail');
    expect(c.channelId).toBe('WEB');
    expect(c.mode).toBe('sandbox');
  });

  it('applies square and paddle sandbox defaults', () => {
    expect(getGatewayConfig('square').environment).toBe('sandbox');
    expect(getGatewayConfig('paddle').environment).toBe('sandbox');
  });
});

describe('getEnabledGateways - launch whitelist', () => {
  it('returns nothing when no keys are configured', () => {
    expect(getEnabledGateways()).toEqual([]);
  });

  it('only activates stripe + paypal even when other gateways have keys', () => {
    process.env.STRIPE_SECRET_KEY = 'sk_test_a';
    process.env.PAYPAL_CLIENT_ID = 'AY1';
    process.env.MOLLIE_API_KEY = 'test_mollie';
    process.env.RAZORPAY_KEY_ID = 'rzp_test';
    const enabled = getEnabledGateways();
    expect(enabled).toContain('stripe');
    expect(enabled).toContain('paypal');
    // mollie/razorpay have valid-looking keys but are not whitelisted for launch
    expect(enabled).not.toContain('mollie');
    expect(enabled).not.toContain('razorpay');
  });

  it('exposes every keyed gateway when PAYMENT_GATEWAYS_ENABLED=all', () => {
    process.env.PAYMENT_GATEWAYS_ENABLED = 'ALL';
    process.env.STRIPE_SECRET_KEY = 'sk_test_a';
    process.env.MOLLIE_API_KEY = 'test_mollie';
    process.env.RAZORPAY_KEY_ID = 'rzp_test';
    const enabled = getEnabledGateways();
    expect(enabled).toContain('mollie');
    expect(enabled).toContain('razorpay');
  });

  it('excludes a whitelisted gateway whose key is only a placeholder', () => {
    process.env.STRIPE_SECRET_KEY = 'your_stripe_key';
    process.env.PAYPAL_CLIENT_ID = 'your_paypal_id';
    expect(getEnabledGateways()).toEqual([]);
  });

  it('tolerates whitespace and empty entries in the flag', () => {
    process.env.PAYMENT_GATEWAYS_ENABLED = ' stripe , , paypal ';
    process.env.STRIPE_SECRET_KEY = 'sk_test_a';
    process.env.PAYPAL_CLIENT_ID = 'AY1';
    expect(getEnabledGateways().sort()).toEqual(['paypal', 'stripe']);
  });
});

describe('isGatewayEnabled', () => {
  it('refuses a non-whitelisted gateway even with a valid key', () => {
    process.env.MOLLIE_API_KEY = 'test_mollie';
    expect(isGatewayEnabled('mollie')).toBe(false);
  });

  it('allows a whitelisted gateway with a valid key', () => {
    process.env.STRIPE_SECRET_KEY = 'sk_test_a';
    expect(isGatewayEnabled('stripe')).toBe(true);
  });

  it('refuses a whitelisted gateway with no key', () => {
    expect(isGatewayEnabled('stripe')).toBe(false);
  });

  it('returns false for an unknown gateway', () => {
    expect(isGatewayEnabled('bitcoin')).toBe(false);
  });

  it('allows a non-whitelisted gateway under the "all" flag', () => {
    process.env.PAYMENT_GATEWAYS_ENABLED = 'all';
    process.env.MOLLIE_API_KEY = 'test_mollie';
    expect(isGatewayEnabled('mollie')).toBe(true);
  });
});

describe('warnLiveKeys', () => {
  it('reports no live mode by default', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    const r = warnLiveKeys();
    expect(r.liveMode).toBe(false);
    expect(r.warnings).toEqual([]);
    expect(warn).not.toHaveBeenCalled();
    warn.mockRestore();
  });

  it('flags a live Stripe key', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    process.env.STRIPE_SECRET_KEY = 'sk_live_abc';
    const r = warnLiveKeys();
    expect(r.liveMode).toBe(true);
    expect(r.warnings[0]).toMatch(/Live key detected/);
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('flags paypal live mode', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    process.env.PAYPAL_MODE = 'LIVE';
    const r = warnLiveKeys();
    expect(r.liveMode).toBe(true);
    expect(r.warnings[0]).toMatch(/PayPal|PAYPAL/);
    warn.mockRestore();
  });

  it('does not flag a test Stripe key', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    process.env.STRIPE_SECRET_KEY = 'sk_test_abc';
    expect(warnLiveKeys().liveMode).toBe(false);
    warn.mockRestore();
  });
});
