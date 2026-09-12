/**
 * Live Commerce API — production-ready order backend for generated storefronts.
 * Zero native dependencies: Express + CORS + JSON-file persistence.
 * Works anywhere Node runs (VPS, Render, Railway, Heroku, cPanel, Vercel functions).
 *
 * Payments: COD/WhatsApp by default. Set STRIPE_SECRET_KEY (+ STRIPE_PUBLISHABLE_KEY)
 * to unlock cards, or PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET to unlock PayPal.
 * Without keys the API keeps working in COD mode — no SDKs required.
 */
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = Number(process.env.PORT || 5000);
const SITE_NAME = process.env.SITE_NAME || 'Store';
const DEFAULT_CURRENCY = process.env.CURRENCY || 'PKR';
const DELIVERY_FEE = Number(process.env.DELIVERY_FEE || 0);
const FREE_DELIVERY_ABOVE = Number(process.env.FREE_DELIVERY_ABOVE || 0);
const WHATSAPP_NUMBER = process.env.WHATSAPP_NUMBER || '';
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'changeme';
const COD_ENABLED = String(process.env.COD_ENABLED || 'true') === 'true';
const APP_BASE_URL = String(process.env.APP_BASE_URL || 'http://localhost:5173').replace(/\/$/, '');
const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY || '';
const STRIPE_PUBLISHABLE_KEY = process.env.STRIPE_PUBLISHABLE_KEY || '';
const PAYPAL_CLIENT_ID = process.env.PAYPAL_CLIENT_ID || '';
const PAYPAL_CLIENT_SECRET = process.env.PAYPAL_CLIENT_SECRET || '';
const PAYPAL_MODE = String(process.env.PAYPAL_MODE || 'live').toLowerCase();

app.use(cors());
app.use(express.json({ limit: '256kb' }));
app.use(express.urlencoded({ extended: true }));

const DATA_DIR = path.join(__dirname, 'data');
const ORDERS_FILE = path.join(DATA_DIR, 'orders.json');
const CATALOG_FILE = path.join(__dirname, '..', 'frontend', 'src', 'data', 'catalog.json');

fs.mkdirSync(DATA_DIR, { recursive: true });
if (!fs.existsSync(ORDERS_FILE)) fs.writeFileSync(ORDERS_FILE, '[]');

function readOrders() {
  try {
    return JSON.parse(fs.readFileSync(ORDERS_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function writeOrders(orders) {
  fs.writeFileSync(ORDERS_FILE, JSON.stringify(orders, null, 2));
}

function loadCatalog() {
  try {
    return JSON.parse(fs.readFileSync(CATALOG_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function money(value) {
  return Math.round((Number(value) || 0) * 100) / 100;
}

// ── Payment gateways (loaded only when enabled by env) ─────────────────────
function stripeSdk() {
  if (!STRIPE_SECRET_KEY) return null;
  try {
    return require('stripe')(STRIPE_SECRET_KEY);
  } catch {
    return null;
  }
}

async function paypalCreateOrder(payload) {
  const mode = PAYPAL_MODE === 'sandbox' ? 'api-m.sandbox.paypal.com' : 'api-m.paypal.com';
  const cred = Buffer.from(`${PAYPAL_CLIENT_ID}:${PAYPAL_CLIENT_SECRET}`).toString('base64');
  const res = await fetch(`https://${mode}/v2/checkout/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${cred}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`paypal create ${res.status}`);
  return res.json();
}

async function paypalCaptureOrder(orderId) {
  const mode = PAYPAL_MODE === 'sandbox' ? 'api-m.sandbox.paypal.com' : 'api-m.paypal.com';
  const cred = Buffer.from(`${PAYPAL_CLIENT_ID}:${PAYPAL_CLIENT_SECRET}`).toString('base64');
  const res = await fetch(`https://${mode}/v2/checkout/orders/${orderId}/capture`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${cred}`,
    },
  });
  if (!res.ok) throw new Error(`paypal capture ${res.status}`);
  return res.json();
}

function paymentMethods() {
  const methods = [];
  if (COD_ENABLED) methods.push('cod');
  if (stripeSdk()) methods.push('stripe');
  if (PAYPAL_CLIENT_ID && PAYPAL_CLIENT_SECRET) methods.push('paypal');
  return methods;
}

// ── Order builder (server-side price recalc from catalog) ──────────────────
function buildOrder(body) {
  const name = String(body.name || '').trim();
  const email = String(body.email || '').trim();
  const phone = String(body.phone || '').trim();
  const address = String(body.address || '').trim();
  const note = String(body.note || '').trim();
  const items = Array.isArray(body.items) ? body.items : [];

  const errors = [];
  if (!name) errors.push('name');
  if (!phone) errors.push('phone');
  if (!items.length) errors.push('items');

  const catalog = loadCatalog();
  const catalogById = new Map(catalog.map((p) => [String(p.id), p]));

  const lineItems = items.map((item) => {
    const id = String(item.id || item.title || '');
    const ref = catalogById.get(id) || item;
    const qty = Math.max(1, Math.min(99, Math.round(Number(item.qty) || 1)));
    const price = money(ref.price ?? item.price ?? 0);
    return {
      id,
      title: ref.title || item.title || 'Item',
      tagline: ref.tagline || '',
      price,
      qty,
      lineTotal: money(price * qty),
    };
  });

  const subtotal = money(lineItems.reduce((sum, l) => sum + l.lineTotal, 0));
  const deliveryFee = money((FREE_DELIVERY_ABOVE > 0 && subtotal >= FREE_DELIVERY_ABOVE) ? 0 : DELIVERY_FEE);
  const total = money(subtotal + deliveryFee);
  const trackingId = 'LD-' + Date.now().toString(36).toUpperCase() + '-' + Math.random().toString(36).slice(2, 6).toUpperCase();

  return {
    order: {
      trackingId,
      createdAt: new Date().toISOString(),
      customer: { name, email, phone, address, note },
      items: lineItems,
      subtotal,
      deliveryFee,
      total,
      currency: DEFAULT_CURRENCY,
      status: 'pending',
    },
    errors,
  };
}

function persistOrder(order, payment) {
  const orders = readOrders();
  order.payment = payment;
  orders.push(order);
  writeOrders(orders);
  return order;
}

app.get('/api/config', (_req, res) => {
  res.json({
    success: true,
    data: {
      siteName: SITE_NAME,
      currency: DEFAULT_CURRENCY,
      deliveryFee: DELIVERY_FEE,
      freeDeliveryAbove: FREE_DELIVERY_ABOVE,
      whatsapp: WHATSAPP_NUMBER,
      paymentMethods: paymentMethods(),
      stripePublishableKey: STRIPE_PUBLISHABLE_KEY,
      paypalClientId: PAYPAL_CLIENT_ID,
    },
  });
});

app.get('/api/products', (_req, res) => {
  const products = loadCatalog();
  res.json({ success: true, data: products, currency: DEFAULT_CURRENCY });
});

// ── Stripe Checkout (hosted page, zero PCI scope on the frontend) ──────────
app.post('/api/payments/stripe/checkout', async (req, res) => {
  try {
    const stripe = stripeSdk();
    if (!stripe) return res.status(503).json({ success: false, error: 'Stripe not configured.' });
    const { order, errors } = buildOrder(req.body || {});
    if (errors.length) return res.status(422).json({ success: false, error: 'Missing fields: ' + errors.join(', ') });

    const session = await stripe.checkout.sessions.create({
      mode: 'payment',
      line_items: order.items.map((l) => ({
        quantity: l.qty,
        price_data: {
          currency: (DEFAULT_CURRENCY || 'USD').toLowerCase(),
          unit_amount: Math.round(l.price * 100),
          product_data: { name: l.title },
        },
      })),
      customer_email: order.customer.email || undefined,
      success_url: `${APP_BASE_URL}/cart?paid=${order.trackingId}&sid={CHECKOUT_SESSION_ID}`,
      cancel_url: `${APP_BASE_URL}/cart`,
      metadata: {
        ref: order.trackingId,
        name: order.customer.name,
        phone: order.customer.phone,
        address: order.customer.address,
        note: order.customer.note,
        items: order.items.map((l) => `${l.id}:${l.qty}`).join('|'),
      },
    });
    res.status(200).json({ success: true, data: { url: session.url, orderId: order.trackingId } });
  } catch (err) {
    res.status(500).json({ success: false, error: 'Stripe session failed.' });
  }
});

app.post('/api/payments/stripe/verify', async (req, res) => {
  try {
    const stripe = stripeSdk();
    if (!stripe) return res.status(503).json({ success: false, error: 'Stripe not configured.' });
    const sessionId = String((req.body || {}).session_id || '');
    if (!sessionId) return res.status(422).json({ success: false, error: 'session_id required.' });
    const session = await stripe.checkout.sessions.retrieve(sessionId);
    if (session.payment_status !== 'paid' || !session.metadata) {
      return res.status(402).json({ success: false, error: 'Payment not completed.' });
    }
    const m = session.metadata;
    const items = String(m.items || '').split('|').filter(Boolean).map((pair) => {
      const [id, qty] = pair.split(':');
      return { id, qty: Number(qty) || 1 };
    });
    const built = buildOrder({ ...m, items });
    const order = built.order;
    order.payment = { method: 'stripe', status: 'paid', stripeSessionId: sessionId, provider: 'stripe' };
    order.status = 'confirmed';
    persistOrder(order, order.payment);
    res.json({ success: true, order });
  } catch (err) {
    res.status(500).json({ success: false, error: 'Stripe verification failed.' });
  }
});

// ── PayPal Orders v2 (REST, no SDK) ────────────────────────────────────────
app.post('/api/payments/paypal/checkout', async (req, res) => {
  try {
    if (!(PAYPAL_CLIENT_ID && PAYPAL_CLIENT_SECRET)) {
      return res.status(503).json({ success: false, error: 'PayPal not configured.' });
    }
    const { order, errors } = buildOrder(req.body || {});
    if (errors.length) return res.status(422).json({ success: false, error: 'Missing fields: ' + errors.join(', ') });
    const paypal = await paypalCreateOrder({
      intent: 'CAPTURE',
      purchase_units: [{
        reference_id: order.trackingId,
        amount: {
          value: order.total.toFixed(2),
          currency_code: (DEFAULT_CURRENCY || 'USD').toUpperCase(),
          breakdown: {
            item_total: { value: order.subtotal.toFixed(2), currency_code: DEFAULT_CURRENCY },
            shipping: { value: order.deliveryFee.toFixed(2), currency_code: DEFAULT_CURRENCY },
          },
        },
        shipping: order.customer.address ? {
          name: { full_name: order.customer.name },
          address: { address_line_1: order.customer.address, country_code: 'US' },
        } : undefined,
      }],
      application_context: {
        brand_name: SITE_NAME,
        user_action: 'PAY_NOW',
        return_url: `${APP_BASE_URL}/cart?paypal=${order.trackingId}`,
        cancel_url: `${APP_BASE_URL}/cart`,
      },
    });
    const approve = (paypal.links || []).find((l) => l.rel === 'approve');
    res.json({ success: true, data: { id: paypal.id, approveUrl: approve ? approve.href : null, orderId: order.trackingId } });
  } catch (err) {
    res.status(500).json({ success: false, error: 'PayPal order creation failed.' });
  }
});

app.post('/api/payments/paypal/capture', async (req, res) => {
  try {
    const paypalId = String((req.body || {}).paypal_id || '');
    if (!paypalId) return res.status(422).json({ success: false, error: 'paypal_id required.' });
    const cap = await paypalCaptureOrder(paypalId);
    if ((cap.status || '').toUpperCase() !== 'COMPLETED') {
      return res.status(402).json({ success: false, error: 'Payment not completed.' });
    }
    const raw = (cap.purchase_units || [{}])[0];
    const ref = raw.reference_id || '';
    const body = {
      name: (req.body || {}).name || '',
      email: (req.body || {}).email || '',
      phone: (req.body || {}).phone || '',
      address: (req.body || {}).address || '',
      note: (req.body || {}).note || '',
      items: (req.body || {}).items || [],
    };
    const { order, errors } = buildOrder(body);
    if (errors.length) return res.status(422).json({ success: false, error: 'Missing fields: ' + errors.join(', ') });
    order.trackingId = ref || order.trackingId;
    order.payment = { method: 'paypal', status: 'paid', paypalOrderId: paypalId, provider: 'paypal' };
    order.status = 'confirmed';
    persistOrder(order, order.payment);
    res.json({ success: true, order });
  } catch (err) {
    res.status(500).json({ success: false, error: 'PayPal capture failed.' });
  }
});

// ── Orders ─────────────────────────────────────────────────────────────────
app.post('/api/orders', (req, res) => {
  const { order, errors } = buildOrder(req.body || {});
  if (errors.length) {
    const messages = {
      name: 'Name and phone are required.', phone: 'Name and phone are required.', items: 'Cart is empty.',
    };
    return res.status(422).json({ success: false, error: messages[errors[0]] || 'Invalid order.' });
  }
  if (!COD_ENABLED) {
    return res.status(503).json({ success: false, error: 'No payment method configured. Set COD_ENABLED=true or add a payment provider.' });
  }
  persistOrder(order, { method: 'cod', status: 'pending' });
  return res.status(201).json({
    success: true,
    order,
    message: 'Order received — pay cash on delivery.',
  });
});

app.get('/api/orders/:trackingId', (req, res) => {
  const orders = readOrders();
  const order = orders.find((o) => o.trackingId === String(req.params.trackingId || ''));
  if (!order) return res.status(404).json({ success: false, error: 'Order not found.' });
  res.json({ success: true, order });
});

app.get('/api/admin/orders', (req, res) => {
  const token = String(req.query.token || '');
  if (!token || token !== ADMIN_TOKEN) return res.status(403).json({ success: false, error: 'Forbidden.' });
  const orders = readOrders();
  const recent = orders.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  res.json({ success: true, count: recent.length, orders: recent });
});

app.get('/api/admin/stats', (req, res) => {
  const token = String(req.query.token || '');
  if (!token || token !== ADMIN_TOKEN) return res.status(403).json({ success: false, error: 'Forbidden.' });
  const orders = readOrders();
  const revenue = money(orders.reduce((sum, o) => sum + o.total, 0));
  const paid = orders.filter((o) => (o.payment || {}).status === 'paid').length;
  const pending = orders.filter((o) => o.status === 'pending').length;
  res.json({ success: true, data: { totalOrders: orders.length, revenue, paid, pending, currency: DEFAULT_CURRENCY } });
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`[commerce] ${SITE_NAME} API listening on port ${PORT}`);
});