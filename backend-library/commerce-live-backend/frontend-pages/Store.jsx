import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ShoppingCart, Plus, Check } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import ButtonMotion from '../components/ui/ButtonMotion';

const FALLBACK_PRODUCTS = [];

export default function Store() {
  const [products, setProducts] = useState(FALLBACK_PRODUCTS);
  const [site, setSite] = useState({ siteName: 'Our Store', currency: 'PKR' });
  const addItem = useAppStore((s) => s.addItem);
  const cart = useAppStore((s) => s.cart);
  const [done, setDone] = useState({});

  useEffect(() => {
    fetch('/api/config')
      .then((r) => r.json())
      .then((res) => {
        if (res.success) setSite(res.data);
      })
      .catch(() => {});
    fetch('/api/products')
      .then((r) => r.json())
      .then((res) => {
        if (res.success && Array.isArray(res.data)) setProducts(res.data);
      })
      .catch(() => {});
  }, []);

  const cartCount = cart.reduce((n, i) => n + (Number(i.qty) || 1), 0);

  return (
    <div className="min-h-screen">
      <nav className="flex items-center justify-between px-6 py-4 bg-slate-900/80 backdrop-blur border-b border-slate-800">
        <Link to="/" className="text-lg font-bold text-cyan-400">
          {site.siteName}
        </Link>
        <div className="flex gap-6 items-center">
          <Link to="/" className="text-sm text-slate-300 hover:text-cyan-400 transition-colors">
            Home
          </Link>
          <Link to="/shop" className="text-sm text-cyan-400 font-medium">
            Shop
          </Link>
          <Link
            to="/cart"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <ShoppingCart className="h-4 w-4" />
            Cart
            {cartCount > 0 && (
              <span className="rounded-full bg-cyan-600 px-2 text-xs font-bold text-white">{cartCount}</span>
            )}
          </Link>
        </div>
      </nav>

      <section className="px-6 py-16 max-w-6xl mx-auto">
        <div className="mb-12 text-center">
          <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-400">
            Order online, pay on delivery
          </span>
          <h1 className="mt-4 text-4xl font-extrabold tracking-tight">Shop Our Products</h1>
          <p className="mx-auto mt-3 max-w-xl text-slate-400">
            Fresh, curated and ready for you. Add items to your cart and complete your order in under
            a minute.
          </p>
        </div>

        {products.length === 0 ? (
          <p className="text-center text-slate-500">
            Catalogue is being prepared — please check back shortly.
          </p>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {products.map((item) => (
              <div
                key={item.id}
                className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-6 hover:border-cyan-500/50 transition-colors"
              >
                <div className="mb-4 flex h-28 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-violet-500/20 text-cyan-300">
                  <ShoppingCart className="h-10 w-10" />
                </div>
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-1 text-sm text-slate-400">{item.tagline}</p>
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-xl font-bold text-cyan-400">
                    {site.currency} {Number(item.price).toLocaleString()}
                  </span>
                  <ButtonMotion
                    onClick={() => {
                      addItem({ ...item, qty: 1 });
                      setDone((d) => ({ ...d, [item.id]: true }));
                      setTimeout(() => setDone((d) => ({ ...d, [item.id]: false })), 1200);
                    }}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-500 transition-colors"
                    aria-label={`Add ${item.title} to cart`}
                  >
                    {done[item.id] ? <Check className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                    {done[item.id] ? 'Added' : 'Add to Cart'}
                  </ButtonMotion>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-sm text-slate-500">
        &copy; {new Date().getFullYear()} {site.siteName}. All rights reserved.
      </footer>
    </div>
  );
}