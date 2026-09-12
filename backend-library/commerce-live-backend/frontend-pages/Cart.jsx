import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Minus, Plus, ShoppingCart, Trash2, Package } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import ButtonMotion from '../components/ui/ButtonMotion';

const statusText = {
  idle: '',
  sending: 'Submitting your orderâ€¦',
  success: 'Order placed successfully!',
  error: 'We could not submit your order. Please try again or contact us on WhatsApp.',
};

export default function Cart() {
  const cart = useAppStore((s) => s.cart);
  const addItem = useAppStore((s) => s.addItem);
  const removeItem = useAppStore((s) => s.removeItem);
  const clearCart = useAppStore((s) => s.clearCart);

  const [site, setSite] = useState({ siteName: 'Our Store', currency: 'PKR', whatsapp: '' });
  const [form, setForm] = useState({ name: '', phone: '', address: '', note: '' });
  const [status, setStatus] = useState('idle');
  const [tracking, setTracking] = useState('');

  useEffect(() => {
    fetch('/api/config')
      .then((r) => r.json())
      .then((res) => {
        if (res.success) setSite(res.data);
      })
      .catch(() => {});
  }, []);

  const subtotal = cart.reduce((sum, i) => sum + (Number(i.price) || 0) * (Number(i.qty) || 1), 0);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.phone.trim()) {
      setStatus('error');
      return;
    }
    setStatus('sending');
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          items: cart.map((i) => ({ id: i.id, title: i.title, price: i.price, qty: i.qty })),
          currency: site.currency,
          total: subtotal,
        }),
      });
      const data = await res.json();
      if (!data.success) throw new Error('order failed');
      setTracking(data.order.trackingId);
      setStatus('success');
      clearCart();
    } catch {
      setStatus('error');
    }
  };

  const cartCount = cart.reduce((n, i) => n + (Number(i.qty) || 1), 0);
  const wa = (site.whatsapp || '').replace(/\D/g, '');
  const waHref =
    'https://wa.me/' + (wa || '0') +
    '?text=' + encodeURIComponent(
      'Hello! I want to order from ' + site.siteName +
      (tracking ? ' (Order ' + tracking + ')' : '') + '. Please confirm my order.'
    );

  return (
    <div className="min-h-screen">
      <nav className="flex items-center justify-between px-6 py-4 bg-slate-900/80 backdrop-blur border-b border-slate-800">
        <Link to="/" className="text-lg font-bold text-cyan-400">
          {site.siteName}
        </Link>
        <div className="flex gap-6 items-center">
          <Link to="/shop" className="text-sm text-slate-300 hover:text-cyan-400 transition-colors">
            Shop
          </Link>
          <Link to="/cart" className="text-sm text-cyan-400 font-medium">
            Cart
          </Link>
        </div>
      </nav>

      <section className="px-6 py-16 max-w-4xl mx-auto">
        {status === 'success' && tracking ? (
          <div className="text-center">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
              <Package className="h-8 w-8" />
            </div>
            <h1 className="text-3xl font-extrabold">Thank you, {form.name}!</h1>
            <p className="mx-auto mt-3 max-w-md text-slate-400">
              Your order is confirmed and pending payment on delivery. Keep your order ID safe:
            </p>
            <div className="mx-auto mt-5 inline-block rounded-lg border border-cyan-500/50 bg-slate-900 px-6 py-3 font-mono text-lg font-bold text-cyan-400">
              {tracking}
            </div>
            <div className="mt-8 flex justify-center gap-4">
              <a
                href={waHref}
                target="_blank"
                rel="noreferrer"
                className="rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-500 transition-colors"
              >
                Confirm on WhatsApp
              </a>
              <Link
                to="/shop"
                className="rounded-lg border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Continue Shopping
              </Link>
            </div>
          </div>
        ) : cart.length === 0 ? (
          <div className="text-center">
            <ShoppingCart className="mx-auto mb-6 h-14 w-14 text-slate-600" />
            <h1 className="text-3xl font-extrabold">Your cart is empty</h1>
            <p className="mx-auto mt-3 max-w-md text-slate-400">
              Add some products from the shop and come back here to place your order.
            </p>
            <Link
              to="/shop"
              className="mt-8 inline-block rounded-lg bg-cyan-600 px-6 py-3 text-sm font-semibold text-white hover:bg-cyan-500 transition-colors"
            >
              Browse the Shop
            </Link>
          </div>
        ) : (
          <div className="grid gap-8 md:grid-cols-5">
            <div className="md:col-span-3">
              <h1 className="mb-6 text-3xl font-extrabold">Your Cart</h1>
              <ul className="space-y-4">
                {cart.map((i) => (
                  <li
                    key={i.id}
                    className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 p-4"
                  >
                    <div>
                      <p className="font-semibold">{i.title}</p>
                      <p className="text-sm text-slate-400">{i.tagline}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <ButtonMotion
                        onClick={() => addItem({ ...i, qty: (Number(i.qty) || 1) - 1 })}
                        className="rounded-md border border-slate-700 p-1.5 text-slate-300 hover:bg-slate-800"
                        aria-label="Decrease quantity"
                      >
                        <Minus className="h-3.5 w-3.5" />
                      </ButtonMotion>
                      <span className="w-6 text-center font-semibold">{i.qty}</span>
                      <ButtonMotion
                        onClick={() => addItem({ ...i, qty: (Number(i.qty) || 1) + 1 })}
                        className="rounded-md border border-slate-700 p-1.5 text-slate-300 hover:bg-slate-800"
                        aria-label="Increase quantity"
                      >
                        <Plus className="h-3.5 w-3.5" />
                      </ButtonMotion>
                      <span className="w-20 text-right font-bold text-cyan-400">
                        {site.currency} {(Number(i.price) * (Number(i.qty) || 1)).toLocaleString()}
                      </span>
                      <ButtonMotion
                        onClick={() => removeItem(i.id)}
                        className="rounded-md p-1.5 text-rose-400 hover:bg-slate-800"
                        aria-label="Remove item"
                      >
                        <Trash2 className="h-4 w-4" />
                      </ButtonMotion>
                    </div>
                  </li>
                ))}
              </ul>
              <div className="mt-6 flex justify-between border-t border-slate-800 pt-4 text-lg font-bold">
                <span>Subtotal</span>
                <span className="text-cyan-400">
                  {site.currency} {subtotal.toLocaleString()}
                </span>
              </div>
            </div>

            <form
              onSubmit={submit}
              className="md:col-span-2 space-y-4 rounded-2xl border border-slate-800 bg-slate-900/50 p-6 self-start"
            >
              <h2 className="text-xl font-bold">Checkout</h2>
              <p className="text-xs text-slate-400">
                Cash on Delivery â€” pay in cash when your order arrives. No card needed.
              </p>
              <input
                value={form.name}
                onChange={set('name')}
                placeholder="Full name *"
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              <input
                value={form.phone}
                onChange={set('phone')}
                placeholder="Phone (03xx-xxxxxxx) *"
                type="tel"
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              <input
                value={form.address}
                onChange={set('address')}
                placeholder="Delivery address"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              <textarea
                value={form.note}
                onChange={set('note')}
                placeholder="Order note (optional)"
                rows={2}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              {status === 'error' && (
                <p className="text-xs text-rose-400" role="alert">
                  {statusText.error}
                </p>
              )}
              <ButtonMotion
                type="submit"
                disabled={status === 'sending'}
                className="w-full rounded-lg bg-cyan-600 px-6 py-3 text-sm font-bold text-white hover:bg-cyan-500 disabled:opacity-60 transition-colors"
              >
                {status === 'sending' ? 'Placing orderâ€¦' : `Place Order â€” ${site.currency} ${subtotal.toLocaleString()}`}
              </ButtonMotion>
            </form>
          </div>
        )}
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-sm text-slate-500">
        &copy; {new Date().getFullYear()} {site.siteName}. All rights reserved.
      </footer>
    </div>
  );
}
