/**
 * CheckoutFlow — single-page conversion-optimized checkout.
 * Auto-generated utility — project primitive.
 * One-page (reduces abandonment), trust badges, order summary,
 * analytics begin_checkout/checkout /purchase pre-wired on the analytics bus.
 */
import { useEffect, useState } from 'react';
import ButtonMotion from '@/components/ui/ButtonMotion';
import { track, trackConversion } from '../../services/analyticsBus';

const TRUST_BADGES = ['SSL Secure', 'PCI-DSS Ready', 'Refund Guarantee', 'GDPR Compliant'];

export default function CheckoutFlow({
  items = [],
  currency = 'USD',
  submitEndpoint = '/api/orders',
  onComplete,
}) {
  const [step, setStep] = useState(1); // 1 contact · 2 payment · 3 review
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [form, setForm] = useState({ email: '', name: '' });
  const subtotal = items.reduce(
    (sum, it) => sum + (Number(it.price) || 0) * (Number(it.qty) || 1),
    0
  );

  useEffect(() => {
    if (items.length) track('begin_checkout', { currency, value: subtotal, items: items.length });
  }, []);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setStatus('sending');
    try {
      const res = await fetch(submitEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, items, currency, total: subtotal }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      trackConversion('purchase', subtotal, currency, { items: items.length });
      setStatus('success');
      if (onComplete) onComplete();
    } catch (err) {
      setStatus('error');
      setError('Payment could not be processed. Please try again.');
    }
  };

  return (
    <div className="fluid-container py-fluid-4">
      <div className="grid gap-8 lg:grid-cols-3">
        <form
          onSubmit={submit}
          className="glass-panel space-y-4 rounded-2xl p-6 lg:col-span-2"
          aria-label="Checkout"
        >
          <ol className="flex gap-2 text-xs">
            {['Contact', 'Payment', 'Review'].map((label, i) => (
              <li key={label} className={i + 1 <= step ? 'text-cyan-400' : 'opacity-50'}>
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
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2"
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
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2"
                />
              </div>
              <div className="flex gap-2">
                <ButtonMotion
                  type="button"
                  onClick={() => setStep(2)}
                  className="rounded-lg bg-cyan-600 px-4 py-2 font-semibold text-white"
                >
                  Continue
                </ButtonMotion>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm" htmlFor="co-card">
                  Card number
                </label>
                <input
                  id="co-card"
                  inputMode="numeric"
                  autoComplete="cc-number"
                  placeholder="4242 4242 4242 4242"
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm" htmlFor="co-exp">
                    Expiry
                  </label>
                  <input
                    id="co-exp"
                    placeholder="MM/YY"
                    autoComplete="cc-exp"
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm" htmlFor="co-cvc">
                    CVC
                  </label>
                  <input
                    id="co-cvc"
                    inputMode="numeric"
                    autoComplete="cc-csc"
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <ButtonMotion
                  type="button"
                  onClick={() => setStep(1)}
                  className="rounded-lg border border-slate-600 px-4 py-2"
                >
                  Back
                </ButtonMotion>
                <ButtonMotion
                  type="button"
                  onClick={() => {
                    track('checkout_progress', { step: 3 });
                    setStep(3);
                  }}
                  className="rounded-lg bg-cyan-600 px-4 py-2 font-semibold text-white"
                >
                  Review
                </ButtonMotion>
              </div>
              <p className="text-xs opacity-70">
                Demo scaffold — integrate a real payment provider before going live.
              </p>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              {error && (
                <p role="alert" className="text-sm text-rose-400">
                  {error}
                </p>
              )}
              <ButtonMotion
                type="submit"
                disabled={status === 'sending'}
                className="w-full rounded-lg bg-emerald-600 px-4 py-3 font-bold text-white transition hover:bg-emerald-500 disabled:opacity-60"
              >
                {status === 'sending'
                  ? 'Processing…'
                  : `Pay ${new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(subtotal)}`}
              </ButtonMotion>
              {status === 'success' && (
                <p role="status" className="text-sm text-emerald-400">
                  Order complete — thank you!
                </p>
              )}
              <ul className="flex flex-wrap gap-2 text-center">
                {TRUST_BADGES.map((b) => (
                  <li
                    key={b}
                    className="rounded-full border border-slate-700 px-3 py-1 text-[11px] opacity-80"
                  >
                    {b}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </form>

        <aside aria-label="Order summary" className="glass-panel h-fit rounded-2xl p-6">
          <h4 className="mb-3 font-semibold">Order summary</h4>
          {items.length === 0 && <p className="text-sm opacity-70">No items yet.</p>}
          <ul className="space-y-2 text-sm">
            {items.map((it, i) => (
              <li key={`${it.id || i}`} className="flex justify-between gap-3">
                <span>
                  {it.name} × {it.qty || 1}
                </span>
                <span>
                  {new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(
                    (Number(it.price) || 0) * (it.qty || 1)
                  )}
                </span>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex justify-between border-t border-slate-800 pt-3 font-semibold">
            <span>Total</span>
            <span>
              {new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(subtotal)}
            </span>
          </div>
        </aside>
      </div>
    </div>
  );
}
