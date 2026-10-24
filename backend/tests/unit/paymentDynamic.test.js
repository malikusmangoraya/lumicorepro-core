/**
 * Unit tests — services/payment/dynamic.js (runtime SystemConfig gateway resolver).
 *
 * Only the external SDK (`stripe`) and the DB-backed SystemConfig service are
 * doubled. `services/payment/config.js` is the REAL env reader, so every
 * "DB value wins / placeholder rejected / env fallback / nothing configured"
 * branch is exercised against production logic instead of a hand-rolled stub.
 */
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

// ── SystemConfig double: honours the real `get(path, fallback)` contract ──────
const configCalls = [];
let DB_VALUES = {};
let configThrows = false;

const systemConfigMock = {
  get: jest.fn(),
  getAll: jest.fn(),
  set: jest.fn(),
};

jest.unstable_mockModule('../../services/systemConfig.service.js', () => ({
  __esModule: true,
  default: systemConfigMock,
}));

// ── Stripe SDK double: records the key each client was built with ────────────
const StripeCtor = jest.fn();
jest.unstable_mockModule('stripe', () => ({
  __esModule: true,
  default: StripeCtor,
}));

const dynamic = await import('../../services/payment/dynamic.js');
const { getGatewayConfig } = await import('../../services/payment/config.js');

const ENV_KEYS = [
  'STRIPE_SECRET_KEY',
  'STRIPE_PUBLISHABLE_KEY',
  'STRIPE_WEBHOOK_SECRET',
  'PAYPAL_CLIENT_ID',
  'PAYPAL_CLIENT_SECRET',
  'PAYPAL_MODE',
  'PAYPAL_WEBHOOK_ID',
  'RAZORPAY_KEY_ID',
  'RAZORPAY_KEY_SECRET',
];

const PLACEHOLDER = 'your_stripe_secret_key';

function setEnv(vars) {
  for (const [key, value] of Object.entries(vars)) {
    if (value === undefined || value === null) delete process.env[key];
    else process.env[key] = String(value);
  }
}

let envSnapshot;

beforeEach(() => {
  envSnapshot = Object.fromEntries(ENV_KEYS.map((k) => [k, process.env[k]]));
  setEnv({
    STRIPE_SECRET_KEY: undefined,
    STRIPE_PUBLISHABLE_KEY: undefined,
    STRIPE_WEBHOOK_SECRET: undefined,
    PAYPAL_CLIENT_ID: undefined,
    PAYPAL_CLIENT_SECRET: undefined,
    PAYPAL_MODE: undefined,
    PAYPAL_WEBHOOK_ID: undefined,
    RAZORPAY_KEY_ID: undefined,
    RAZORPAY_KEY_SECRET: undefined,
  });

  DB_VALUES = {};
  configThrows = false;
  configCalls.length = 0;
  // Bind the implementation here: jest.config sets resetMocks/clearMocks, so a
  // top-level implementation would be stripped before every test.
  systemConfigMock.get.mockImplementation(async (path = '', fallback) => {
    configCalls.push({ path, fallback });
    if (configThrows) throw new Error('system config unavailable');
    return path in DB_VALUES ? DB_VALUES[path] : fallback;
  });
  StripeCtor.mockImplementation((key) => ({ __stripeKey: key }));
});

afterEach(() => {
  setEnv(envSnapshot);
});

/** Paths SystemConfig was asked for in this test. */
const requestedPaths = () => configCalls.map((c) => c.path);

describe('getStripeClient', () => {
  it('builds the client from the runtime SystemConfig key, ignoring env', async () => {
    setEnv({ STRIPE_SECRET_KEY: 'sk_test_from_env' });
    DB_VALUES['payments.stripe'] = { secretKey: 'sk_test_from_db' };

    const client = await dynamic.getStripeClient();

    expect(client).toEqual({ __stripeKey: 'sk_test_from_db' });
    expect(StripeCtor).toHaveBeenCalledTimes(1);
    expect(StripeCtor).toHaveBeenCalledWith('sk_test_from_db');
    expect(systemConfigMock.get).toHaveBeenCalledWith('payments.stripe', {});
  });

  it('rejects a DB placeholder and falls back to a real env key', async () => {
    DB_VALUES['payments.stripe'] = { secretKey: PLACEHOLDER };
    setEnv({ STRIPE_SECRET_KEY: 'sk_test_real_env' });

    const client = await dynamic.getStripeClient();
    expect(client).toEqual({ __stripeKey: 'sk_test_real_env' });
  });

  it('returns null when SystemConfig holds no row at all and env is unset', async () => {
    // `get()` resolves to the `{}` fallback — the absent-config branch
    const client = await dynamic.getStripeClient();

    expect(client).toBeNull();
    expect(StripeCtor).not.toHaveBeenCalled();
    expect(requestedPaths()).toEqual(['payments.stripe']);
  });

  it('returns null when every configured key is still a your_ placeholder', async () => {
    DB_VALUES['payments.stripe'] = { secretKey: 'your_key_here' };
    setEnv({ STRIPE_SECRET_KEY: 'your_key_here' });

    expect(await dynamic.getStripeClient()).toBeNull();
    expect(StripeCtor).not.toHaveBeenCalled();
  });

  it('returns null (never throws) when the SDK constructor rejects the key', async () => {
    DB_VALUES['payments.stripe'] = { secretKey: 'sk_test_weird' };
    StripeCtor.mockImplementation(() => {
      throw new TypeError('Invalid API key');
    });

    expect(await dynamic.getStripeClient()).toBeNull();
    expect(StripeCtor).toHaveBeenCalledWith('sk_test_weird');
  });
});

describe('Stripe publishable + webhook secrets', () => {
  it('prefers the DB publishable key over env', async () => {
    DB_VALUES['payments.stripe'] = { publishableKey: 'pk_test_db' };
    setEnv({ STRIPE_PUBLISHABLE_KEY: 'pk_test_env' });

    expect(await dynamic.getStripePublishableKey()).toBe('pk_test_db');
  });

  it('falls back to env, then to an empty string', async () => {
    setEnv({ STRIPE_PUBLISHABLE_KEY: 'pk_test_env' });
    expect(await dynamic.getStripePublishableKey()).toBe('pk_test_env');

    setEnv({ STRIPE_PUBLISHABLE_KEY: undefined });
    expect(await dynamic.getStripePublishableKey()).toBe('');
  });

  it('resolves the webhook secret from DB then env, never placeholders', async () => {
    DB_VALUES['payments.stripe'] = { webhookSecret: 'whsec_db' };
    expect(await dynamic.getStripeWebhookSecret()).toBe('whsec_db');

    DB_VALUES['payments.stripe'] = {};
    setEnv({ STRIPE_WEBHOOK_SECRET: 'whsec_env' });
    expect(await dynamic.getStripeWebhookSecret()).toBe('whsec_env');

    setEnv({ STRIPE_WEBHOOK_SECRET: undefined });
    expect(await dynamic.getStripeWebhookSecret()).toBe('');
  });
});

describe('getGatewayRuntimeConfig — stripe', () => {
  it('is enabled only when a usable secret AND a publishable key exist', async () => {
    DB_VALUES['payments.stripe'] = {
      secretKey: 'sk_test_db',
      publishableKey: 'pk_test_db',
      webhookSecret: 'whsec_db',
      mode: 'live',
    };

    expect(await dynamic.getGatewayRuntimeConfig('stripe')).toEqual({
      enabled: true,
      secretKey: 'sk_test_db',
      publishableKey: 'pk_test_db',
      webhookSecret: 'whsec_db',
      mode: 'live',
    });
  });

  it('stays disabled when the secret is present but the publishable key is not', async () => {
    setEnv({ STRIPE_SECRET_KEY: 'sk_test_env' });
    const runtime = await dynamic.getGatewayRuntimeConfig('stripe');

    expect(runtime.enabled).toBe(false);
    expect(runtime.secretKey).toBe('sk_test_env');
    expect(runtime.publishableKey).toBe('');
    expect(runtime.mode).toBe('sandbox');
  });

  it('merges env over an absent SystemConfig row and defaults mode to sandbox', async () => {
    setEnv({
      STRIPE_SECRET_KEY: 'sk_test_env',
      STRIPE_PUBLISHABLE_KEY: 'pk_test_env',
      STRIPE_WEBHOOK_SECRET: 'whsec_env',
    });

    expect(await dynamic.getGatewayRuntimeConfig('stripe')).toEqual({
      enabled: true,
      secretKey: 'sk_test_env',
      publishableKey: 'pk_test_env',
      webhookSecret: 'whsec_env',
      mode: 'sandbox',
    });
  });

  it('produces an empty config when nothing is configured anywhere', async () => {
    expect(await dynamic.getGatewayRuntimeConfig('stripe')).toEqual({
      enabled: false,
      secretKey: '',
      publishableKey: '',
      webhookSecret: '',
      mode: 'sandbox',
    });
  });
});

describe('getGatewayRuntimeConfig — paypal', () => {
  it('reads DB credentials and mode', async () => {
    DB_VALUES['payments.paypal'] = {
      clientId: 'client_db',
      clientSecret: 'secret_db',
      mode: 'live',
      webhookId: 'wh_db',
    };

    expect(await dynamic.getGatewayRuntimeConfig('paypal')).toEqual({
      enabled: true,
      clientId: 'client_db',
      clientSecret: 'secret_db',
      mode: 'live',
      webhookId: 'wh_db',
    });
  });

  it('falls back to env values when the DB row is absent', async () => {
    setEnv({
      PAYPAL_CLIENT_ID: 'client_env',
      PAYPAL_CLIENT_SECRET: 'secret_env',
      PAYPAL_MODE: 'live',
      PAYPAL_WEBHOOK_ID: 'wh_env',
    });

    expect(await dynamic.getGatewayRuntimeConfig('paypal')).toEqual({
      enabled: true,
      clientId: 'client_env',
      clientSecret: 'secret_env',
      mode: 'live',
      webhookId: 'wh_env',
    });
  });

  it('is disabled when only one half of the credential pair exists', async () => {
    DB_VALUES['payments.paypal'] = { clientId: 'client_db' };

    const runtime = await dynamic.getGatewayRuntimeConfig('paypal');
    expect(runtime.enabled).toBe(false);
    expect(runtime.clientId).toBe('client_db');
    expect(runtime.clientSecret).toBe('');
    expect(runtime.mode).toBe('sandbox');
    expect(runtime.webhookId).toBe('');
  });

  it('drops your_ placeholders from DB and env', async () => {
    DB_VALUES['payments.paypal'] = { clientId: 'your_client_id', clientSecret: 'your_secret' };
    setEnv({ PAYPAL_CLIENT_ID: 'your_client_id', PAYPAL_CLIENT_SECRET: 'your_secret' });

    const runtime = await dynamic.getGatewayRuntimeConfig('paypal');
    expect(runtime).toEqual({
      enabled: false,
      clientId: '',
      clientSecret: '',
      mode: 'sandbox',
      webhookId: '',
    });
  });
});

describe('getGatewayRuntimeConfig — non-Stripe/PayPal gateways', () => {
  it('returns the env config untouched for other gateways', async () => {
    setEnv({ RAZORPAY_KEY_ID: 'rzp_key', RAZORPAY_KEY_SECRET: 'rzp_secret' });

    const runtime = await dynamic.getGatewayRuntimeConfig('razorpay');

    // Documented gap: razorpay (and the other 9 gateways) never consult
    // SystemConfig, so admin-panel keys cannot reach them through this layer.
    expect(runtime).toEqual(getGatewayConfig('razorpay'));
    expect(runtime.enabled).toBe(true);
    expect(runtime.keyId).toBe('rzp_key');
    expect(requestedPaths()).toEqual([]);
  });

  it('returns an empty object for an unknown gateway instead of throwing', async () => {
    expect(await dynamic.getGatewayRuntimeConfig('bitcoin')).toEqual({});
    expect(requestedPaths()).toEqual([]);
  });
});

describe('gatewayReady', () => {
  it('returns ok for a fully configured runtime gateway', async () => {
    DB_VALUES['payments.stripe'] = { secretKey: 'sk_test_db', publishableKey: 'pk_test_db' };
    expect(await dynamic.gatewayReady('stripe')).toEqual({ ok: true });
  });

  it('returns the operator-facing message when the gateway is unconfigured', async () => {
    expect(await dynamic.gatewayReady('stripe')).toEqual({
      ok: false,
      message: dynamic.UNCONFIGURED_MESSAGE,
    });
  });

  it('reports not-ready for an unknown gateway', async () => {
    const result = await dynamic.gatewayReady('bitcoin');
    expect(result.ok).toBe(false);
    expect(result.message).toBe(
      'Payment system unconfigured. Please insert your keys in the Admin Settings panel.',
    );
  });

  it('is not ready when only env carries a placeholder key', async () => {
    setEnv({ STRIPE_SECRET_KEY: PLACEHOLDER });
    expect(await dynamic.gatewayReady('stripe')).toEqual({
      ok: false,
      message: dynamic.UNCONFIGURED_MESSAGE,
    });
  });

  it('is ready for razorpay purely from env (no SystemConfig read)', async () => {
    setEnv({ RAZORPAY_KEY_ID: 'rzp_key' });
    expect(await dynamic.gatewayReady('razorpay')).toEqual({ ok: true });
    expect(requestedPaths()).toEqual([]);
  });
});
