import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Minus, Plus, ShoppingCart, Trash2, Package, CreditCard } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import ButtonMotion from '../components/ui/ButtonMotion';

const STRINGS = {
  en: {
    shop: 'Shop', cart: 'Cart', thankYou: 'Thank you', orderPending: 'Your order is confirmed.',
    orderPaid: 'Your payment was received and your order is confirmed.',
    keepId: 'Keep your order ID safe:', confirmWhatsApp: 'Confirm on WhatsApp', continueShopping: 'Continue Shopping',
    emptyCart: 'Your cart is empty', emptyCartHint: 'Add some products from the shop and come back to place your order.',
    browseShop: 'Browse the Shop', yourCart: 'Your Cart', subtotal: 'Subtotal', checkout: 'Checkout',
    deliveredPayCash: 'Cash on delivery — pay in cash when your order arrives. No card needed.',
    fullName: 'Full name', phone: 'Phone number', address: 'Delivery address', note: 'Order note (optional)',
    orderError: 'We could not submit your order. Please try again.', placing: 'Placing order…',
    placeOrder: 'Place Order', paymentMethod: 'Payment method', cod: 'Cash on Delivery', stripe: 'Card (Stripe)',
    paypal: 'PayPal', language: 'Language', cardNote: 'You will be redirected to a secure Stripe checkout page.',
    paypalNote: 'You will be redirected to PayPal to approve your payment.', orderSuccess: 'Order placed successfully!',
  },
  ur: {
    shop: 'دکان', cart: 'کارٹ', thankYou: 'شکریہ', orderPending: 'آپ کا آرڈر تصدیق شدہ ہے۔',
    orderPaid: 'آپ کی ادائیگی مل گئی اور آرڈر تصدیق شدہ ہے۔',
    keepId: 'اپنا آرڈر آئی ڈی محفوظ رکھیں:', confirmWhatsApp: 'واٹس ایپ پر تصدیق', continueShopping: 'مزید خریداری',
    emptyCart: 'آپ کی کارٹ خالی ہے', emptyCartHint: 'دکان سے کچھ پراڈکٹس شامل کریں اور واپس آ کر آرڈر دیں۔',
    browseShop: 'دکان دیکھیں', yourCart: 'آپ کی کارٹ', subtotal: 'مجموعی', checkout: 'چیک آؤٹ',
    deliveredPayCash: 'ڈیلیوری پر کیش — آرڈر پہنچنے پر کیش ادا کریں۔ کسی کارڈ کی ضرورت نہیں۔',
    fullName: 'پورا نام', phone: 'فون نمبر', address: 'ڈیلیوری ایڈریس', note: 'آرڈر نوٹ (اختیاری)',
    orderError: 'ہم آپ کا آرڈر جمع نہیں کر سکے۔ دوبارہ کوشش کریں۔', placing: 'آرڈر ہو رہا ہے…',
    placeOrder: 'آرڈر دیں', paymentMethod: 'ادائیگی کا طریقہ', cod: 'کیش آن ڈیلیوری', stripe: 'کارڈ (اسٹرائپ)',
    paypal: 'پے پال', language: 'زبان', cardNote: 'آپ کو محفوظ اسٹرائپ چیک آؤٹ پر لے جایا جائے گا۔',
    paypalNote: 'آپ کو پے پال پر ادائیگی کی تصدیق کے لیے لے جایا جائے گا۔', orderSuccess: 'آرڈر کامیابی سے ہو گیا!',
  },
  es: {
    shop: 'Tienda', cart: 'Carrito', thankYou: 'Gracias', orderPending: 'Tu pedido está confirmado.',
    orderPaid: 'Recibimos tu pago y tu pedido está confirmado.',
    keepId: 'Guarda tu ID de pedido:', confirmWhatsApp: 'Confirmar por WhatsApp', continueShopping: 'Seguir comprando',
    emptyCart: 'Tu carrito está vacío', emptyCartHint: 'Añade productos de la tienda y vuelve para hacer tu pedido.',
    browseShop: 'Ver la tienda', yourCart: 'Tu carrito', subtotal: 'Subtotal', checkout: 'Pago',
    deliveredPayCash: 'Pago contra entrega — paga en efectivo cuando llegue tu pedido. Sin tarjeta.',
    fullName: 'Nombre completo', phone: 'Teléfono', address: 'Dirección de entrega', note: 'Nota (opcional)',
    orderError: 'No pudimos enviar tu pedido. Inténtalo de nuevo.', placing: 'Enviando pedido…',
    placeOrder: 'Realizar pedido', paymentMethod: 'Método de pago', cod: 'Contra reembolso', stripe: 'Tarjeta (Stripe)',
    paypal: 'PayPal', language: 'Idioma', cardNote: 'Serás redirigido a la pasarela segura de Stripe.',
    paypalNote: 'Serás redirigido a PayPal para aprobar tu pago.', orderSuccess: '¡Pedido realizado!',
  },
  fr: {
    shop: 'Boutique', cart: 'Panier', thankYou: 'Merci', orderPending: 'Votre commande est confirmée.',
    orderPaid: 'Votre paiement a été reçu et votre commande est confirmée.',
    keepId: 'Conservez votre numéro de commande :', confirmWhatsApp: 'Confirmer sur WhatsApp', continueShopping: 'Continuer vos achats',
    emptyCart: 'Votre panier est vide', emptyCartHint: 'Ajoutez des produits de la boutique puis revenez commander.',
    browseShop: 'Voir la boutique', yourCart: 'Votre panier', subtotal: 'Sous-total', checkout: 'Paiement',
    deliveredPayCash: 'Paiement à la livraison — payez en espèces à la réception. Aucune carte requise.',
    fullName: 'Nom complet', phone: 'Téléphone', address: 'Adresse de livraison', note: 'Note (facultatif)',
    orderError: "Impossible d'envoyer votre commande. Réessayez.", placing: 'Envoi de la commande…',
    placeOrder: 'Passer la commande', paymentMethod: 'Mode de paiement', cod: 'Paiement à la livraison', stripe: 'Carte (Stripe)',
    paypal: 'PayPal', language: 'Langue', cardNote: 'Vous serez redirigé vers le paiement sécurisé Stripe.',
    paypalNote: 'Vous serez redirigé vers PayPal pour approuver votre paiement.', orderSuccess: 'Commande passée !',
  },
  de: {
    shop: 'Shop', cart: 'Warenkorb', thankYou: 'Danke', orderPending: 'Ihre Bestellung ist bestätigt.',
    orderPaid: 'Ihre Zahlung ist eingegangen und die Bestellung ist bestätigt.',
    keepId: 'Bewahren Sie Ihre Bestellnummer auf:', confirmWhatsApp: 'Per WhatsApp bestätigen', continueShopping: 'Weiter einkaufen',
    emptyCart: 'Ihr Warenkorb ist leer', emptyCartHint: 'Fügen Sie Produkte aus dem Shop hinzu und kehren Sie zurück, um zu bestellen.',
    browseShop: 'Zum Shop', yourCart: 'Ihr Warenkorb', subtotal: 'Zwischensumme', checkout: 'Kasse',
    deliveredPayCash: 'Barzahlung bei Lieferung — zahlen Sie bar, wenn Ihre Bestellung ankommt. Keine Karte nötig.',
    fullName: 'Vollständiger Name', phone: 'Telefonnummer', address: 'Lieferadresse', note: 'Notiz (optional)',
    orderError: 'Ihre Bestellung konnte nicht übermittelt werden. Versuchen Sie es erneut.', placing: 'Bestellung wird gesendet…',
    placeOrder: 'Bestellung aufgeben', paymentMethod: 'Zahlungsart', cod: 'Nachnahme', stripe: 'Karte (Stripe)',
    paypal: 'PayPal', language: 'Sprache', cardNote: 'Sie werden zum sicheren Stripe-Bezahlvorgang weitergeleitet.',
    paypalNote: 'Sie werden zu PayPal weitergeleitet, um die Zahlung zu bestätigen.', orderSuccess: 'Bestellung erfolgreich!',
  },
};
const LANGS = ['en', 'ur', 'es', 'fr', 'de'];

export default function Cart() {
  const cart = useAppStore((s) => s.cart);
  const addItem = useAppStore((s) => s.addItem);
  const removeItem = useAppStore((s) => s.removeItem);
  const clearCart = useAppStore((s) => s.clearCart);

  const [sp] = useSearchParams();
  const [lang, setLang] = useState(() => localStorage.getItem('lmc_lang') || 'en');
  const t = useMemo(() => {
    const dict = STRINGS[lang] || STRINGS.en;
    return (k) => dict[k] || STRINGS.en[k] || k;
  }, [lang]);

  const [site, setSite] = useState({ siteName: 'Our Store', currency: 'PKR', whatsapp: '', paymentMethods: ['cod'] });
  const [method, setMethod] = useState('cod');
  const [form, setForm] = useState({ name: '', phone: '', address: '', note: '', email: '' });
  const [status, setStatus] = useState('idle');
  const [tracking, setTracking] = useState('');
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    localStorage.setItem('lmc_lang', lang);
  }, [lang]);

  useEffect(() => {
    fetch('/api/config')
      .then((r) => r.json())
      .then((res) => {
        if (res.success) {
          setSite(res.data);
          const methods = res.data.paymentMethods || ['cod'];
          setMethod(methods[0] || 'cod');
        }
      })
      .catch(() => {});
  }, []);

  // Stripe / PayPal success return handling.
  useEffect(() => {
    const paidRef = sp.get('paid');
    const sid = sp.get('sid');
    const paypalRef = sp.get('paypal');
    const token = sp.get('token');
    if (paidRef && sid) {
      setStatus('sending');
      fetch('/api/payments/stripe/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid }),
      })
        .then((r) => r.json())
        .then((data) => {
          setTracking(paidRef);
          setStatus(data.success ? 'success' : 'error');
        })
        .catch(() => setStatus('error'))
        .finally(() => setChecking(false));
      return;
    }
    if (paypalRef && token) {
      const saved = JSON.parse(sessionStorage.getItem('lmc_pp_' + paypalRef) || '{}');
      if (!saved.items) {
        setChecking(false);
        return;
      }
      setStatus('sending');
      fetch('/api/payments/paypal/capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...saved, paypal_id: token }),
      })
        .then((r) => r.json())
        .then((data) => {
          setTracking(data.order?.trackingId || paypalRef);
          setStatus(data.success ? 'success' : 'error');
          clearCart();
        })
        .catch(() => setStatus('error'))
        .finally(() => setChecking(false));
      return;
    }
    setChecking(false);
  }, [sp]);

  useEffect(() => {
    if (sp.get('paid') && !sp.get('sid')) setChecking(false);
  }, []);

  const subtotal = cart.reduce((sum, i) => sum + (Number(i.price) || 0) * (Number(i.qty) || 1), 0);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.phone.trim()) {
      setStatus('error');
      return;
    }
    const payload = {
      name: form.name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim(),
      address: form.address.trim(),
      note: form.note.trim(),
      items: cart.map((i) => ({ id: i.id, title: i.title, price: i.price, qty: i.qty })),
      currency: site.currency,
      total: subtotal,
    };
    setStatus('sending');
    if (method === 'stripe') {
      try {
        const res = await fetch('/api/payments/stripe/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.success || !data.data?.url) throw new Error('stripe failed');
        window.location.href = data.data.url;
      } catch {
        setStatus('error');
      }
      return;
    }
    if (method === 'paypal') {
      try {
        const res = await fetch('/api/payments/paypal/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.success || !data.data?.approveUrl) throw new Error('paypal failed');
        sessionStorage.setItem('lmc_pp_' + data.data.orderId, JSON.stringify(payload));
        window.location.href = data.data.approveUrl;
      } catch {
        setStatus('error');
      }
      return;
    }
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
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

  const payOk = status === 'success';
  const processing = status === 'sending' || checking || cartCount === 0;

  return (
    <div className="min-h-screen">
      <nav className="flex items-center justify-between px-6 py-4 bg-slate-900/80 backdrop-blur border-b border-slate-800">
        <Link to="/" className="text-lg font-bold text-cyan-400">
          {site.siteName}
        </Link>
        <div className="flex gap-6 items-center">
          <Link to="/shop" className="text-sm text-slate-300 hover:text-cyan-400 transition-colors">
            {t('shop')}
          </Link>
          <Link to="/cart" className="text-sm text-cyan-400 font-medium">
            {t('cart')}
          </Link>
          <label className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>{t('language')}</span>
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500"
              aria-label="Language"
            >
              {LANGS.map((l) => (
                <option key={l} value={l}>{l.toUpperCase()}</option>
              ))}
            </select>
          </label>
        </div>
      </nav>

      <section className="px-6 py-16 max-w-4xl mx-auto">
        {payOk && tracking ? (
          <div className="text-center">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
              <Package className="h-8 w-8" />
            </div>
            <h1 className="text-3xl font-extrabold">{t('thankYou')}, {form.name || ''}</h1>
            <p className="mx-auto mt-3 max-w-md text-slate-400">{t('orderPending')}</p>
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
                {t('confirmWhatsApp')}
              </a>
              <Link
                to="/shop"
                className="rounded-lg border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors"
              >
                {t('continueShopping')}
              </Link>
            </div>
          </div>
        ) : cart.length === 0 && !processing ? (
          <div className="text-center">
            <ShoppingCart className="mx-auto mb-6 h-14 w-14 text-slate-600" />
            <h1 className="text-3xl font-extrabold">{t('emptyCart')}</h1>
            <p className="mx-auto mt-3 max-w-md text-slate-400">
              {t('emptyCartHint')}
            </p>
            <Link
              to="/shop"
              className="mt-8 inline-block rounded-lg bg-cyan-600 px-6 py-3 text-sm font-semibold text-white hover:bg-cyan-500 transition-colors"
            >
              {t('browseShop')}
            </Link>
          </div>
        ) : (
          <div className="grid gap-8 md:grid-cols-5">
            <div className="md:col-span-3">
              <h1 className="mb-6 text-3xl font-extrabold">{t('yourCart')}</h1>
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
                <span>{t('subtotal')}</span>
                <span className="text-cyan-400">
                  {site.currency} {subtotal.toLocaleString()}
                </span>
              </div>
            </div>

            <form
              onSubmit={submit}
              className="md:col-span-2 space-y-4 rounded-2xl border border-slate-800 bg-slate-900/50 p-6 self-start"
            >
              <h2 className="text-xl font-bold">{t('checkout')}</h2>

              <fieldset>
                <legend className="mb-2 text-sm font-semibold text-slate-300">{t('paymentMethod')}</legend>
                <div className="space-y-2">
                  {(site.paymentMethods || ['cod']).map((m) => (
                    <label
                      key={m}
                      className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                        method === m ? 'border-cyan-500 bg-cyan-950/40 text-cyan-300' : 'border-slate-700 text-slate-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="method"
                        value={m}
                        checked={method === m}
                        onChange={() => setMethod(m)}
                        className="accent-cyan-500"
                      />
                      {m === 'stripe' && <CreditCard className="h-4 w-4" />}
                      {t(m)}
                    </label>
                  ))}
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {method === 'cod' && t('deliveredPayCash')}
                  {method === 'stripe' && t('cardNote')}
                  {method === 'paypal' && t('paypalNote')}
                </p>
              </fieldset>

              <input
                value={form.name}
                onChange={set('name')}
                placeholder={t('fullName') + ' *'}
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              <input
                value={form.phone}
                onChange={set('phone')}
                placeholder={t('phone') + ' *'}
                type="tel"
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              <input
                value={form.email}
                onChange={set('email')}
                placeholder="Email (optional)"
                type="email"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              <input
                value={form.address}
                onChange={set('address')}
                placeholder={t('address')}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              <textarea
                value={form.note}
                onChange={set('note')}
                placeholder={t('note')}
                rows={2}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500"
              />
              {status === 'error' && (
                <p className="text-xs text-rose-400" role="alert">
                  {t('orderError')}
                </p>
              )}
              <ButtonMotion
                type="submit"
                disabled={status === 'sending'}
                className="w-full rounded-lg bg-cyan-600 px-6 py-3 text-sm font-bold text-white hover:bg-cyan-500 disabled:opacity-60 transition-colors"
              >
                {status === 'sending' ? t('placing') : `${t('placeOrder')} — ${site.currency} ${subtotal.toLocaleString()}`}
              </ButtonMotion>
            </form>
          </div>
        )}
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-sm text-slate-500">
        &copy; {new Date().getFullYear()} {site.siteName}. <span>All rights reserved.</span>
      </footer>
    </div>
  );
}