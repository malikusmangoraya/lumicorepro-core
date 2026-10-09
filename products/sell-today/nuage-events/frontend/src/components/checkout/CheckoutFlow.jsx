/**
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
                  `Pay ${new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(subtotal)}`}
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
