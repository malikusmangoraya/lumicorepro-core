/**
 * Live Commerce API — production-ready order backend for generated storefronts.
 * Zero native dependencies: Express + CORS + JSON-file persistence.
 * Works anywhere Node runs (VPS, Render, Railway, Heroku, cPanel, Vercel functions).
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

app.get('/api/config', (_req, res) => {
  res.json({
    success: true,
    data: {
      siteName: SITE_NAME,
      currency: DEFAULT_CURRENCY,
      deliveryFee: DELIVERY_FEE,
      freeDeliveryAbove: FREE_DELIVERY_ABOVE,
      whatsapp: WHATSAPP_NUMBER,
      paymentMethods: (COD_ENABLED ? ['cod'] : []).concat([]),
    },
  });
});

app.get('/api/products', (_req, res) => {
  const products = loadCatalog();
  res.json({ success: true, data: products, currency: DEFAULT_CURRENCY });
});

app.post('/api/orders', (req, res) => {
  const body = req.body || {};
  const name = String(body.name || '').trim();
  const email = String(body.email || '').trim();
  const phone = String(body.phone || '').trim();
  const address = String(body.address || '').trim();
  const note = String(body.note || '').trim();
  const items = Array.isArray(body.items) ? body.items : [];

  if (!name || !phone) {
    return res.status(422).json({ success: false, error: 'Name and phone are required.' });
  }
  if (!items.length) {
    return res.status(422).json({ success: false, error: 'Cart is empty.' });
  }

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
  const order = {
    trackingId,
    createdAt: new Date().toISOString(),
    customer: { name, email, phone, address, note },
    items: lineItems,
    subtotal,
    deliveryFee,
    total,
    currency: DEFAULT_CURRENCY,
    payment: { method: COD_ENABLED ? 'cod' : '', status: COD_ENABLED ? 'pending' : 'unpaid' },
    status: 'pending',
  };

  if (COD_ENABLED) {
    const orders = readOrders();
    orders.push(order);
    writeOrders(orders);
    return res.status(201).json({
      success: true,
      order: order,
      message: 'Order received — pay cash on delivery.',
    });
  }

  res.status(503).json({ success: false, error: 'No payment method configured. Set COD_ENABLED=true or add a payment provider.' });
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
  const pending = orders.filter((o) => o.status === 'pending').length;
  res.json({ success: true, data: { totalOrders: orders.length, revenue, pending, currency: DEFAULT_CURRENCY } });
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`[commerce] ${SITE_NAME} API listening on port ${PORT}`);
});