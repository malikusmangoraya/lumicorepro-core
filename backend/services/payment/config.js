/**
 * Payment Gateway Configuration
 * Reads and validates gateway API keys from environment
 */

const getGatewayConfig = (gateway) => {
  const configs = {
    stripe: {
      enabled: Boolean(
        process.env.STRIPE_SECRET_KEY && 
        !process.env.STRIPE_SECRET_KEY.includes('your_')
      ),
      publishableKey: process.env.STRIPE_PUBLISHABLE_KEY,
      secretKey: process.env.STRIPE_SECRET_KEY,
      webhookSecret: process.env.STRIPE_WEBHOOK_SECRET,
    },
    paypal: {
      enabled: Boolean(
        process.env.PAYPAL_CLIENT_ID && 
        !process.env.PAYPAL_CLIENT_ID.includes('your_')
      ),
      clientId: process.env.PAYPAL_CLIENT_ID,
      clientSecret: process.env.PAYPAL_CLIENT_SECRET,
      mode: process.env.PAYPAL_MODE || 'sandbox',
      webhookId: process.env.PAYPAL_WEBHOOK_ID,
    },
    razorpay: {
      enabled: Boolean(
        process.env.RAZORPAY_KEY_ID && 
        !process.env.RAZORPAY_KEY_ID.includes('your_')
      ),
      keyId: process.env.RAZORPAY_KEY_ID,
      keySecret: process.env.RAZORPAY_KEY_SECRET,
      webhookSecret: process.env.RAZORPAY_WEBHOOK_SECRET,
    },
    square: {
      enabled: Boolean(
        process.env.SQUARE_ACCESS_TOKEN && 
        !process.env.SQUARE_ACCESS_TOKEN.includes('your_')
      ),
      accessToken: process.env.SQUARE_ACCESS_TOKEN,
      locationId: process.env.SQUARE_LOCATION_ID,
      environment: process.env.SQUARE_ENVIRONMENT || 'sandbox',
    },
    bkash: {
      enabled: Boolean(
        process.env.BKASH_APP_KEY && 
        !process.env.BKASH_APP_KEY.includes('your_')
      ),
      appKey: process.env.BKASH_APP_KEY,
      appSecret: process.env.BKASH_APP_SECRET,
      username: process.env.BKASH_USERNAME,
      password: process.env.BKASH_PASSWORD,
      merchantId: process.env.BKASH_MERCHANT_ID,
    },
    mercadopago: {
      enabled: Boolean(
        process.env.MERCADOPAGO_ACCESS_TOKEN && 
        !process.env.MERCADOPAGO_ACCESS_TOKEN.includes('your_')
      ),
      accessToken: process.env.MERCADOPAGO_ACCESS_TOKEN,
      publicKey: process.env.MERCADOPAGO_PUBLIC_KEY,
      webhookPassword: process.env.MERCADOPAGO_WEBHOOK_PASSWORD,
    },
    flutterwave: {
      enabled: Boolean(
        process.env.FLUTTERWAVE_SECRET_KEY && 
        !process.env.FLUTTERWAVE_SECRET_KEY.includes('your_')
      ),
      publicKey: process.env.FLUTTERWAVE_PUBLIC_KEY,
      secretKey: process.env.FLUTTERWAVE_SECRET_KEY,
      encryptionKey: process.env.FLUTTERWAVE_ENCRYPTION_KEY,
      webhookSecret: process.env.FLUTTERWAVE_WEBHOOK_SECRET,
    },
    paytm: {
      enabled: Boolean(
        process.env.PAYTM_MERCHANT_ID && 
        !process.env.PAYTM_MERCHANT_ID.includes('your_')
      ),
      merchantId: process.env.PAYTM_MERCHANT_ID,
      merchantKey: process.env.PAYTM_MERCHANT_KEY,
      website: process.env.PAYTM_WEBSITE || 'WEBSTAGING',
      industryType: process.env.PAYTM_INDUSTRY_TYPE || 'Retail',
      channelId: process.env.PAYTM_CHANNEL_ID || 'WEB',
      mode: process.env.PAYTM_MODE || 'sandbox',
    },
    mollie: {
      enabled: Boolean(
        process.env.MOLLIE_API_KEY && 
        !process.env.MOLLIE_API_KEY.includes('your_')
      ),
      apiKey: process.env.MOLLIE_API_KEY,
      organizationId: process.env.MOLLIE_ORGANIZATION_ID,
    },
    liqpay: {
      enabled: Boolean(
        process.env.LIQPAY_PUBLIC_KEY && 
        !process.env.LIQPAY_PUBLIC_KEY.includes('your_')
      ),
      publicKey: process.env.LIQPAY_PUBLIC_KEY,
      privateKey: process.env.LIQPAY_PRIVATE_KEY,
    },
    paddle: {
      enabled: Boolean(
        process.env.PADDLE_API_KEY && 
        !process.env.PADDLE_API_KEY.includes('your_')
      ),
      apiKey: process.env.PADDLE_API_KEY,
      webhookSecret: process.env.PADDLE_WEBHOOK_SECRET,
      environment: process.env.PADDLE_ENV || 'sandbox',
    },
  };
  return configs[gateway] || null;
};

const getEnabledGateways = () => {
  const gateways = [
    'stripe', 'paypal', 'razorpay', 'square', 'bkash',
    'mercadopago', 'flutterwave', 'paytm', 'mollie', 'liqpay', 'paddle'
  ];

  // --- LAUNCH FEATURE FLAG ---
  // At launch we only activate Stripe + PayPal. The other 11 gateways stay
  // implemented in code but disabled: they will NOT return from this function,
  // won't appear in the checkout UI, and won't process refunds.
  //
  //   env value                              -> active gateways
  //   PAYMENT_GATEWAYS_ENABLED=stripe,paypal -> stripe + paypal (launch default)
  //   PAYMENT_GATEWAYS_ENABLED=all           -> every gateway with a valid key
  //   (unset)                                -> every gateway with a valid key
  //
  // To enable another gateway later: add its slug below, e.g. stripe,paypal,paddle.
  // Comment: "disabled for launch — enable when gateway-specific demand confirmed"
  const launchWhitelist = ['stripe', 'paypal'];
  const enabledFlag = (process.env.PAYMENT_GATEWAYS_ENABLED || '')
    .toLowerCase()
    .split(',')
    .map((g) => g.trim())
    .filter(Boolean);

  if (enabledFlag.includes('all')) {
    // Explicit opt-in to all gateways (dev/live testing only)
    return gateways.filter((gateway) => {
      const config = getGatewayConfig(gateway);
      return config && config.enabled;
    });
  }

  return gateways
    .filter((gateway) => launchWhitelist.includes(gateway))
    .filter((gateway) => {
      const config = getGatewayConfig(gateway);
      return config && config.enabled;
    });
};

const isGatewayEnabled = (gateway) => {
  const enabledFlag = (process.env.PAYMENT_GATEWAYS_ENABLED || '')
    .toLowerCase()
    .split(',')
    .map((g) => g.trim())
    .filter(Boolean);
  const launchWhitelist = ['stripe', 'paypal'];
  if (!enabledFlag.includes('all') && !launchWhitelist.includes(gateway)) {
    return false;
  }
  const config = getGatewayConfig(gateway);
  return config ? config.enabled : false;
};

/**
 * Startup safety check — logs a warning whenever LIVE keys are detected.
 * Currently all gateways default to sandbox/test in .env.example.
 * When you go live, replace this with a hard check or add an
 * environment variable: PAYMENT_LIVE_MODE=true
 */
export function warnLiveKeys() {
  const warnings = [];
  const stripeKey = process.env.STRIPE_SECRET_KEY || '';
  const paypalMode = (process.env.PAYPAL_MODE || 'sandbox').toLowerCase();

  if (stripeKey.startsWith('sk_live')) {
    warnings.push('STRIPE: Live key detected (sk_live_...) — real charges will occur!');
  }
  if (paypalMode === 'live') {
    warnings.push('PAYPAL: Live mode — real payments will process');
  }
  if (warnings.length > 0) {
    console.warn('\n⚠️  PAYMENT LIVE MODE WARNING:\n' + warnings.join('\n') + '\n');
  }
  return { liveMode: warnings.length > 0, warnings };
}

export {
  getGatewayConfig,
  getEnabledGateways,
  isGatewayEnabled
};

export default {
  getGatewayConfig,
  getEnabledGateways,
  isGatewayEnabled
};