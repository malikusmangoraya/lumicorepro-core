/**
 * real-payments.cjs — the frontend of the payment flow stops pretending.
 *
 * Before: `lib/paymentProvider.js` was `class MockPaymentProvider` returning
 * `id: 'mock-checkout-session'` (and nothing imported it), while `CheckoutFlow` collected
 * raw card number / expiry / CVC in the browser and POSTed them to `/api/orders`. That is
 * both fake and a PCI-DSS violation.
 *
 * After: a gateway client over the endpoints this app already ships
 * (`/api/payment/config`, `/api/payment/checkout`, `/api/lemonsqueezy/config`,
 * `/api/lemonsqueezy/checkout`) and a checkout that hands off to the gateway's own hosted
 * page. Card data never reaches the product's own code, and an unconfigured deployment
 * says so instead of faking a charge.
 *
 * Run: node products/_audit/real-payments.cjs
 */
const fs = require('fs');

const PRODUCTS = [
  'apex',
  'aurelia-estates',
  'aurum-fitness',
  'claimflow-ai',
  'flowpilot',
  'meridian-capital',
  'nuage-events',
  'prestige-studio',
  'resupro',
  'saffron-voyage',
  'studio-lumen',
];

const PAYMENT_PROVIDER = `/**
 * Payment gateway client.
 * ----------------------
 * The browser never sees a gateway secret and never handles card data: this module talks to
 * the app's own Express backend, which is the only place a secret is read, and the browser is
 * then redirected to the gateway's hosted checkout page.
 *
 * Endpoints (see backend/routes/payment.routes.js and backend/routes/lemonsqueezy.routes.js):
 *   GET  /api/payment/config          which gateways are live, plus publishable keys
 *   POST /api/payment/checkout        Stripe Checkout session for a plan or an order
 *   POST /api/payment/portal          Stripe Billing Portal (subscription management)
 *   GET  /api/lemonsqueezy/config     merchant-of-record storefront config
 *   POST /api/lemonsqueezy/checkout   Lemon Squeezy hosted checkout (works signed out)
 *
 * A gateway that is not configured answers 503 with \`configured: false\`; that surfaces here
 * as PaymentNotConfiguredError, so a storefront can tell "no keys yet" apart from "broken"
 * instead of silently showing a demo dialog.
 */
import { getApiConfig } from '../services/apiConfig';

const { API_URL } = getApiConfig();

export const GATEWAYS = {
  stripe: 'stripe',
  paypal: 'paypal',
  paddle: 'paddle',
  lemonsqueezy: 'lemonsqueezy',
};

export class PaymentNotConfiguredError extends Error {
  constructor(message) {
    super(message || 'Online payment is not configured for this deployment yet.');
    this.name = 'PaymentNotConfiguredError';
    this.code = 'PAYMENT_UNCONFIGURED';
  }
}

export class PaymentRequestError extends Error {
  constructor(message, options) {
    super(message || 'The payment service could not complete the request.');
    this.name = 'PaymentRequestError';
    this.code = options?.status ? \`PAYMENT_HTTP_\${options.status}\` : 'PAYMENT_REQUEST_FAILED';
  }
}

const authToken = () => {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage.getItem('auth_token');
  } catch {
    return null;
  }
};

async function request(path, { method = 'GET', body } = {}) {
  const token = authToken();
  let response;
  try {
    response = await fetch(\`\${API_URL}\${path}\`, {
      method,
      headers: {
        Accept: 'application/json',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: \`Bearer \${token}\` } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  } catch (cause) {
    throw new PaymentRequestError(
      'Could not reach the payment service. Check your connection and try again.',
      { cause }
    );
  }

  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = {};
  }

  if (response.status === 503 || payload.configured === false) {
    throw new PaymentNotConfiguredError(
      payload.error || payload.unconfiguredMessage || 'Online payment is not configured yet.'
    );
  }
  if (!response.ok) {
    throw new PaymentRequestError(
      payload.error || \`The payment service rejected the request (HTTP \${response.status}).\`,
      { status: response.status }
    );
  }
  return payload;
}

export const paymentProvider = {
  /** Which gateways this deployment actually has keys for. */
  async getConfig() {
    return request('/payment/config');
  },

  /** Merchant-of-record storefront config (store id, whether the webhook is verified). */
  async getLemonSqueezyConfig() {
    try {
      return await request('/lemonsqueezy/config');
    } catch (error) {
      if (error instanceof PaymentNotConfiguredError) return { configured: false };
      throw error;
    }
  },

  /** Stripe Checkout session. Resolves to the hosted URL to send the buyer to. */
  async createStripeCheckout({ planId, orderId, successUrl, cancelUrl, agentApiKey } = {}) {
    const payload = await request('/payment/checkout', {
      method: 'POST',
      body: { planId, orderId, successUrl, cancelUrl, agentApiKey },
    });
    return { gateway: GATEWAYS.stripe, url: payload.checkoutUrl, sessionId: payload.sessionId, mode: payload.mode };
  },

  /** Lemon Squeezy hosted checkout. Works for signed-out visitors. */
  async createLemonSqueezyCheckout({
    variantId,
    planName,
    amount,
    currency,
    orderId,
    email,
    redirectUrl,
    customData,
  } = {}) {
    const payload = await request('/lemonsqueezy/checkout', {
      method: 'POST',
      body: { variantId, planName, amount, currency, orderId, email, redirectUrl, customData },
    });
    return { gateway: GATEWAYS.lemonsqueezy, url: payload.url, mode: payload.mode, paymentId: payload.paymentId };
  },

  /** Stripe Billing Portal, for changing or cancelling an existing subscription. */
  async createPortalSession() {
    const payload = await request('/payment/portal', { method: 'POST', body: {} });
    return { url: payload.url };
  },

  /**
   * Picks a configured gateway and opens its checkout.
   *
   * \`gateway: 'auto'\` prefers Stripe for signed-in buyers (it can attach the payment to
   * their account) and Lemon Squeezy otherwise, because its route accepts anonymous buyers.
   */
  async createCheckoutSession(options = {}) {
    const { gateway = 'auto', amount, currency, planName, orderId, email, successUrl, cancelUrl } = options;
    const signedIn = Boolean(authToken());

    const wantsStripe = gateway === GATEWAYS.stripe || (gateway === 'auto' && signedIn);
    const attempts = wantsStripe
      ? [
          () => this.createStripeCheckout({ planId: options.planId, orderId, successUrl, cancelUrl }),
          () => this.createLemonSqueezyCheckout({ variantId: options.variantId, planName, amount, currency, orderId, email }),
        ]
      : [
          () => this.createLemonSqueezyCheckout({ variantId: options.variantId, planName, amount, currency, orderId, email }),
          () => this.createStripeCheckout({ planId: options.planId, orderId, successUrl, cancelUrl }),
        ];

    const failures = [];
    for (const attempt of attempts) {
      try {
        const session = await attempt();
        if (session?.url) return session;
        failures.push('the gateway returned no checkout URL');
      } catch (error) {
        failures.push(error.message);
      }
    }

    throw new PaymentNotConfiguredError(
      failures.filter(Boolean).join(' ') || 'No payment gateway is configured for this deployment.'
    );
  },
};

export default paymentProvider;
`;

const CHECKOUT_FLOW = `/**
 * CheckoutFlow — single-page, conversion-oriented checkout.
 *
 * The buyer enters contact details here, then pays on the gateway's own hosted page:
 * no card number, expiry or CVC is ever typed into, posted to, or stored by this app. The
 * flow reads the deployment's live gateway config first, so a store with no keys says
 * "payment is not configured" instead of appearing to take money.
 */
import { useEffect, useState } from 'react';
import ButtonMotion from '@/components/ui/ButtonMotion';
import { track, trackConversion } from '../../services/analyticsBus';
import paymentProvider, { PaymentNotConfiguredError } from '../../lib/paymentProvider';

const TRUST_BADGES = ['SSL Secure', 'PCI-DSS (gateway hosted)', 'Refund Guarantee', 'GDPR Compliant'];

export default function CheckoutFlow({
  items = [],
  currency = 'USD',
  gateway = 'auto',
  planName = '',
  orderId,
  onComplete,
}) {
  const [step, setStep] = useState(1); // 1 contact · 2 method · 3 review + pay
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [gateways, setGateways] = useState(null); // null = probing, {} = answer received
  const [form, setForm] = useState({ email: '', name: '' });
  const subtotal = items.reduce((sum, it) => sum + (Number(it.price) || 0) * (Number(it.qty) || 1), 0);

  useEffect(() => {
    if (items.length) track('begin_checkout', { currency, value: subtotal, items: items.length });
  }, []);

  useEffect(() => {
    let cancelled = false;
    paymentProvider
      .getConfig()
      .then((config) => {
        if (!cancelled) setGateways(config?.gateways || {});
      })
      .catch((configError) => {
        if (!cancelled) setGateways({ __error: configError.message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const set = (key) => (event) => setForm((previous) => ({ ...previous, [key]: event.target.value }));
  const liveGateways = Object.entries(gateways || {}).filter(([, value]) => value?.enabled);

  const submit = async (event) => {
    event.preventDefault();
    setStatus('sending');
    setError('');
    try {
      const session = await paymentProvider.createCheckoutSession({
        gateway,
        planId: undefined,
        orderId,
        amount: subtotal,
        currency,
        planName,
        email: form.email,
      });
      trackConversion('begin_payment', subtotal, currency, { gateway: session.gateway, items: items.length });
      setStatus('redirecting');
      window.location.assign(session.url);
    } catch (submitError) {
      setStatus('error');
      setError(
        submitError instanceof PaymentNotConfiguredError
          ? submitError.message
          : submitError.message || 'Payment could not be started. Please try again.'
      );
    }
  };

  return (
    <div className="fluid-container py-10">
      <div className="grid gap-8 lg:grid-cols-3">
        <form onSubmit={submit} className="card-panel space-y-4 p-6 lg:col-span-2" aria-label="Checkout">
          <ol className="flex gap-2 text-xs">
            {['Contact', 'Payment method', 'Review'].map((label, i) => (
              <li
                key={label}
                style={{ color: i + 1 <= step ? 'var(--t-primary)' : 'var(--t-muted)' }}
              >
                {i + 1}. {label}
                {i < 2 ? ' ·' : ''}
              </li>
            ))}
          </ol>

          {step === 1 && (
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm" htmlFor="co-email">
                  Email
                </label>
                <input
                  id="co-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={form.email}
                  onChange={set('email')}
                  className="w-full rounded-lg border p-2"
                  style={{ borderColor: 'var(--t-border)', background: 'var(--t-surface)', color: 'var(--t-text)' }}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm" htmlFor="co-name">
                  Full name
                </label>
                <input
                  id="co-name"
                  required
                  autoComplete="name"
                  value={form.name}
                  onChange={set('name')}
                  className="w-full rounded-lg border p-2"
                  style={{ borderColor: 'var(--t-border)', background: 'var(--t-surface)', color: 'var(--t-text)' }}
                />
              </div>
              <ButtonMotion type="button" className="btn-primary" onClick={() => setStep(2)}>
                Continue
              </ButtonMotion>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              {gateways === null && <p className="text-sm">Checking which payment methods are available…</p>}
              {gateways && liveGateways.length === 0 && (
                <p role="alert" className="text-sm" style={{ color: 'var(--t-muted)' }}>
                  No payment gateway is configured for this deployment yet. The server enables gateways
                  through <code>PAYMENT_GATEWAYS_ENABLED</code> and their keys in <code>.env</code>; once
                  they are set, this step lists them automatically.
                </p>
              )}
              {liveGateways.length > 0 && (
                <ul className="space-y-2 text-sm">
                  {liveGateways.map(([name, config]) => (
                    <li key={name} className="flex items-center justify-between rounded-lg border p-3" style={{ borderColor: 'var(--t-border)' }}>
                      <span className="font-medium capitalize">{name}</span>
                      <span style={{ color: 'var(--t-muted)' }}>
                        {(config.methods || []).slice(0, 3).join(', ') || config.mode || 'hosted checkout'}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <p className="text-xs" style={{ color: 'var(--t-muted)' }}>
                Card details are entered on the gateway's own secure page, never on this site.
              </p>
              <div className="flex gap-2">
                <ButtonMotion type="button" className="btn-outline" onClick={() => setStep(1)}>
                  Back
                </ButtonMotion>
                <ButtonMotion
                  type="button"
                  className="btn-primary"
                  onClick={() => {
                    track('checkout_progress', { step: 3 });
                    setStep(3);
                  }}
                >
                  Review
                </ButtonMotion>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              {error && (
                <p role="alert" className="text-sm" style={{ color: 'var(--t-accent)' }}>
                  {error}
                </p>
              )}
              <ButtonMotion type="submit" disabled={status === 'sending' || status === 'redirecting'} className="btn-primary w-full justify-center">
                {status === 'sending' && 'Starting secure checkout…'}
                {status === 'redirecting' && 'Redirecting to the payment page…'}
                {status !== 'sending' &&
                  status !== 'redirecting' &&
                  \`Pay \${new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(subtotal)}\`}
              </ButtonMotion>
              <ul className="flex flex-wrap gap-2 text-center">
                {TRUST_BADGES.map((badge) => (
                  <li key={badge} className="rounded-full border px-3 py-1 text-[11px]" style={{ borderColor: 'var(--t-border)', color: 'var(--t-muted)' }}>
                    {badge}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </form>

        <aside aria-label="Order summary" className="card-panel h-fit p-6">
          <h4 className="mb-3 font-semibold">Order summary</h4>
          {items.length === 0 && <p className="text-sm" style={{ color: 'var(--t-muted)' }}>No items yet.</p>}
          <ul className="space-y-2 text-sm">
            {items.map((item, i) => (
              <li key={item.id || i} className="flex justify-between gap-3">
                <span>
                  {item.name} × {item.qty || 1}
                </span>
                <span>
                  {new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(
                    (Number(item.price) || 0) * (item.qty || 1)
                  )}
                </span>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex justify-between border-t pt-3 font-semibold" style={{ borderColor: 'var(--t-border)' }}>
            <span>Total</span>
            <span>{new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(subtotal)}</span>
          </div>
          {planName && <p className="mt-2 text-xs" style={{ color: 'var(--t-muted)' }}>{planName}</p>}
        </aside>
      </div>
    </div>
  );
}
`;

const report = [];
for (const id of PRODUCTS) {
  const src = `products/${id}/frontend/src`;
  const provider = `${src}/lib/paymentProvider.js`;
  const flow = `${src}/components/checkout/CheckoutFlow.jsx`;

  fs.writeFileSync(provider, PAYMENT_PROVIDER.replace(/\n/g, '\r\n'));
  fs.writeFileSync(flow, CHECKOUT_FLOW.replace(/\n/g, '\r\n'));

  const providerText = fs.readFileSync(provider, 'utf8');
  const flowText = fs.readFileSync(flow, 'utf8');
  report.push({
    id,
    providerLines: providerText.split(/\r?\n/).length,
    flowLines: flowText.split(/\r?\n/).length,
    mockGone: !/MockPaymentProvider|mock-checkout-session/.test(providerText),
    // Looks for card *input markers*, not the words: the new flow documents that it does not
    // collect card data, and a naive word match flags that sentence.
    noPan: !/autoComplete="cc-|id="co-card"|id="co-cvc"|placeholder="4242/.test(flowText),
    callsRealApi:
      providerText.includes('/payment/config') &&
      providerText.includes('/lemonsqueezy/checkout') &&
      !providerText.includes('mock-checkout-session'),
    honestUnconfigured: /PaymentNotConfiguredError/.test(providerText) && /PaymentNotConfiguredError/.test(flowText),
  });
}

console.log('product            | provider | flow | no mock | no PAN/CVC | real endpoints | honest unconfigured');
console.log('-------------------|----------|------|---------|------------|----------------|--------------------');
for (const r of report) {
  console.log(
    `${r.id.padEnd(18)} | ${String(r.providerLines).padStart(8)} | ${String(r.flowLines).padStart(4)} | ${r.mockGone ? '  ok    ' : '  NO    '} | ${r.noPan ? '   ok      ' : '   NO       '} | ${r.callsRealApi ? '     ok       ' : '     NO       '} | ${r.honestUnconfigured ? 'ok' : 'NO'}`
  );
}
const failed = report.filter((r) => !(r.mockGone && r.noPan && r.callsRealApi && r.honestUnconfigured));
console.log(`\n${report.length - failed.length}/${report.length} payment front ends replaced`);
process.exitCode = failed.length ? 1 : 0;
