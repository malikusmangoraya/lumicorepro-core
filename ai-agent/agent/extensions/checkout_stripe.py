"""Generate a persisted, provider-backed Stripe checkout only when requested."""
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from utils.logger import agent_logger


_INTENTS_ROUTE = """const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth');
const {
  createCheckoutSession,
  getOrderStatus,
  handleStripeWebhook,
} = require('../services/stripeService');

router.post('/checkout-session', protect, async (req, res, next) => {
  try {
    const result = await createCheckoutSession(req.user.id);
    res.status(201).json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
});

router.get('/orders/:orderId', protect, async (req, res, next) => {
  try {
    const result = await getOrderStatus(req.params.orderId, req.user.id);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
});

router.post('/webhook', express.raw({ type: 'application/json' }), async (req, res, next) => {
  try {
    const result = await handleStripeWebhook(
      req.rawBody || req.body,
      req.headers['stripe-signature']
    );
    res.json(result);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
"""

_SERVICE = """const Stripe = require('stripe');
const { QueryTypes } = require('sequelize');
const { randomUUID } = require('crypto');
const { sequelize } = require('../config/database');

const getStripe = () => {
  if (!process.env.STRIPE_SECRET_KEY) {
    throw new Error('STRIPE_SECRET_KEY is required before checkout can be used.');
  }
  return new Stripe(process.env.STRIPE_SECRET_KEY, { apiVersion: '2024-06-20' });
};

async function createCheckoutSession(userId) {
  if (!process.env.STRIPE_PRICE_ID) {
    throw new Error('STRIPE_PRICE_ID is required before checkout can be used.');
  }
  if (!process.env.STRIPE_SUCCESS_URL || !process.env.STRIPE_CANCEL_URL) {
    throw new Error('STRIPE_SUCCESS_URL and STRIPE_CANCEL_URL are required.');
  }
  const stripe = getStripe();
  return sequelize.transaction(async (transaction) => {
    const orderId = randomUUID();
    const successUrl = new URL(process.env.STRIPE_SUCCESS_URL);
    successUrl.searchParams.set('order_id', orderId);
    await sequelize.query(
      `INSERT INTO orders (id, user_id, status, created_at, updated_at)
       VALUES (:id, :userId, 'pending', NOW(), NOW())`,
      { replacements: { id: orderId, userId }, transaction }
    );
    const session = await stripe.checkout.sessions.create(
      {
        mode: 'payment',
        line_items: [{ price: process.env.STRIPE_PRICE_ID, quantity: 1 }],
        client_reference_id: orderId,
        success_url: successUrl.toString(),
        cancel_url: process.env.STRIPE_CANCEL_URL,
      },
      { idempotencyKey: `checkout:${orderId}` }
    );
    if (!session.id || !session.url) {
      throw new Error('Stripe did not return a usable checkout session.');
    }
    await sequelize.query(
      'UPDATE orders SET stripe_checkout_session_id = :sessionId, updated_at = NOW() WHERE id = :orderId',
      { replacements: { sessionId: session.id, orderId }, transaction }
    );
    return { order_id: orderId, checkout_url: session.url };
  });
}

async function getOrderStatus(orderId, userId) {
  const orders = await sequelize.query(
    `SELECT id, status, amount_total, currency FROM orders
     WHERE id = :orderId AND user_id = :userId`,
    {
      replacements: { orderId, userId },
      type: QueryTypes.SELECT,
    }
  );
  if (!orders.length) {
    const error = new Error('Order was not found.');
    error.statusCode = 404;
    throw error;
  }
  return orders[0];
}

async function handleStripeWebhook(rawBody, signature) {
  if (!process.env.STRIPE_WEBHOOK_SECRET) {
    throw new Error('STRIPE_WEBHOOK_SECRET is required to verify payment events.');
  }
  if (!signature || !Buffer.isBuffer(rawBody)) {
    throw new Error('A Stripe signature and raw request body are required.');
  }
  const event = getStripe().webhooks.constructEvent(
    rawBody,
    signature,
    process.env.STRIPE_WEBHOOK_SECRET
  );
  return sequelize.transaction(async (transaction) => {
    const inserted = await sequelize.query(
      `INSERT INTO payment_events (event_id, event_type, created_at)
       VALUES (:eventId, :eventType, NOW())
       ON CONFLICT (event_id) DO NOTHING
       RETURNING event_id`,
      {
        replacements: { eventId: event.id, eventType: event.type },
        type: QueryTypes.SELECT,
        transaction,
      }
    );
    if (!inserted.length) {
      return { success: true, received: true, verified: true, duplicate: true };
    }
    const session = event.data.object;
    if (
      event.type === 'checkout.session.completed' &&
      session.payment_status === 'paid'
    ) {
      const updatedOrders = await sequelize.query(
        `UPDATE orders SET status = 'paid', amount_total = :amount, currency = :currency,
         updated_at = NOW() WHERE id = :orderId AND stripe_checkout_session_id = :sessionId
         AND status = 'pending' RETURNING id`,
        {
          replacements: {
            amount: session.amount_total,
            currency: session.currency,
            orderId: session.client_reference_id,
            sessionId: session.id,
          },
          type: QueryTypes.SELECT,
          transaction,
        }
      );
      if (!updatedOrders.length) {
        throw new Error('Verified Stripe checkout does not match a pending order.');
      }
    } else if (event.type === 'checkout.session.expired') {
      await sequelize.query(
        `UPDATE orders SET status = 'expired', updated_at = NOW()
         WHERE id = :orderId AND stripe_checkout_session_id = :sessionId AND status = 'pending'`,
        {
          replacements: { orderId: session.client_reference_id, sessionId: session.id },
          transaction,
        }
      );
    }
    return { success: true, received: true, verified: true, event_type: event.type };
  });
}

module.exports = { createCheckoutSession, getOrderStatus, handleStripeWebhook };
"""

_PAYMENT_MIGRATION = """module.exports = {
  up: async ({ queryInterface, Sequelize, transaction }) => {
    await queryInterface.createTable('orders', {
      id: { type: Sequelize.UUID, primaryKey: true, allowNull: false },
      user_id: { type: Sequelize.UUID, allowNull: false },
      status: { type: Sequelize.STRING(24), allowNull: false, defaultValue: 'pending' },
      stripe_checkout_session_id: { type: Sequelize.STRING(255), unique: true },
      amount_total: { type: Sequelize.INTEGER },
      currency: { type: Sequelize.STRING(3) },
      created_at: { type: Sequelize.DATE, allowNull: false },
      updated_at: { type: Sequelize.DATE, allowNull: false },
    }, { transaction });
    await queryInterface.createTable('payment_events', {
      event_id: { type: Sequelize.STRING(255), primaryKey: true, allowNull: false },
      event_type: { type: Sequelize.STRING(100), allowNull: false },
      created_at: { type: Sequelize.DATE, allowNull: false },
    }, { transaction });
  },
  down: async ({ queryInterface, transaction }) => {
    await queryInterface.dropTable('payment_events', { transaction });
    await queryInterface.dropTable('orders', { transaction });
  },
};
"""

_ENV_ADD = """
# Stripe Checkout — set credentials from the Stripe Dashboard.
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID=
STRIPE_SUCCESS_URL=http://localhost:5173/payment/success
STRIPE_CANCEL_URL=http://localhost:5173/cart
"""

_README_SECTION = """
## Payments (Stripe Checkout)

Configure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID`,
`STRIPE_SUCCESS_URL`, and `STRIPE_CANCEL_URL` in the backend environment. The
server creates an authenticated checkout session using the configured Stripe
Price ID. The return page confirms status through the authenticated API instead
of trusting the redirect. Order state changes only after a valid Stripe webhook;
webhook event IDs are stored uniquely so retries cannot apply payment state twice. Without
valid provider configuration, checkout and webhook requests return errors and
do not claim success. Use Stripe test mode and verify webhook delivery before
launching.
"""


def _payment_features(project_dir: Path, requested: List[str] | None) -> set[str]:
    if requested is not None:
        features = requested
    else:
        report = project_dir / "generation-report.json"
        if not report.is_file():
            return set()
        data = json.loads(report.read_text(encoding="utf-8"))
        features = data.get("features") or data.get("spec", {}).get("features") or []
    if isinstance(features, str):
        features = [features]
    return {str(feature).strip().lower() for feature in features if str(feature).strip()}


class CheckoutScaffolder:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)

    def scaffold(self, features: List[str] | None = None) -> Dict[str, Any]:
        if not self.project_dir.is_dir():
            return {"status": "failed", "message": "Project directory not found"}
        if "stripe_payments" not in _payment_features(self.project_dir, features):
            return {
                "status": "skipped",
                "message": "Stripe payments were not explicitly requested; payment scaffold skipped.",
            }

        backend = self.project_dir / "backend"
        if not backend.is_dir():
            return {"status": "failed", "message": "Full-stack backend is required for payments."}
        created: List[str] = []
        services = backend / "services"
        routes = backend / "routes"
        migrations = backend / "migrations"
        for folder in (services, routes, migrations):
            folder.mkdir(parents=True, exist_ok=True)

        generated_files = {
            services / "stripeService.js": _SERVICE,
            routes / "stripeRoutes.js": _INTENTS_ROUTE,
            migrations / "002_payment_events.js": _PAYMENT_MIGRATION,
        }
        for path, content in generated_files.items():
            if not path.is_file():
                path.write_text(content, encoding="utf-8")
                created.append(path.relative_to(self.project_dir).as_posix())

        env = backend / ".env.example"
        env.parent.mkdir(parents=True, exist_ok=True)
        env_text = env.read_text(encoding="utf-8") if env.is_file() else ""
        if "STRIPE_PRICE_ID" not in env_text:
            env.write_text(env_text.rstrip() + "\n" + _ENV_ADD, encoding="utf-8")
            created.append("backend/.env.example (updated)")

        package_path = backend / "package.json"
        if package_path.is_file():
            package = json.loads(package_path.read_text(encoding="utf-8"))
            dependencies = package.setdefault("dependencies", {})
            dependencies.setdefault("stripe", "^16.0.0")
            package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")

        server = backend / "server.js"
        if server.is_file():
            source = server.read_text(encoding="utf-8")
            if "stripeRoutes" not in source:
                if "require('dotenv').config();" not in source or "// Error Handling" not in source:
                    raise ValueError("Cannot safely mount Stripe routes into backend/server.js.")
                source = source.replace(
                    "require('dotenv').config();",
                    "require('dotenv').config();\nconst stripeRoutes = require('./routes/stripeRoutes');",
                )
                source = source.replace(
                    "app.use(express.json());",
                    "app.use(express.json({ verify: (req, res, buffer) => { req.rawBody = Buffer.from(buffer); } }));",
                )
                source = source.replace(
                    "// Error Handling",
                    "app.use('/api/payments', stripeRoutes);\n\n// Error Handling",
                )
                server.write_text(source, encoding="utf-8")
                created.append("backend/server.js (payments route mounted)")

        frontend_button = (
            self.project_dir
            / "frontend"
            / "src"
            / "components"
            / "ecommerce"
            / "GeneratedCheckoutButton.jsx"
        )
        if (self.project_dir / "frontend").is_dir() and not frontend_button.is_file():
            frontend_button.parent.mkdir(parents=True, exist_ok=True)
            frontend_button.write_text(
                """import React, { useState } from 'react';

export default function GeneratedCheckoutButton({ children = 'Checkout', className = '' }) {
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function beginCheckout() {
    setError('');
    setSubmitting(true);
    try {
      const response = await fetch('/api/payments/checkout-session', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('auth_token')
            ? { Authorization: `Bearer ${localStorage.getItem('auth_token')}` }
            : {}),
        },
        body: '{}',
      });
      const result = await response.json();
      if (!response.ok || !result.success || !result.data?.checkout_url) {
        throw new Error(result.message || 'Checkout could not be started.');
      }
      window.location.assign(result.data.checkout_url);
    } catch (checkoutError) {
      setError(checkoutError.message || 'Checkout could not be started.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <button type="button" className={className} disabled={submitting} onClick={beginCheckout}>
        {submitting ? 'Connecting to secure checkout…' : children}
      </button>
      {error && <p role="alert">{error}</p>}
    </>
  );
}
""",
                encoding="utf-8",
            )
            created.append("frontend/src/components/ecommerce/GeneratedCheckoutButton.jsx")

        frontend_src = self.project_dir / "frontend" / "src"
        if frontend_src.is_dir():
            pages = frontend_src / "pages"
            pages.mkdir(parents=True, exist_ok=True)
            checkout_page = pages / "GeneratedCheckoutPage.jsx"
            if not checkout_page.is_file():
                checkout_page.write_text(
                    """import React from 'react';
import { Link } from 'react-router-dom';
import GeneratedCheckoutButton from '../components/ecommerce/GeneratedCheckoutButton';

export default function GeneratedCheckoutPage() {
  return (
    <main className="mx-auto flex min-h-[70vh] w-full max-w-xl items-center px-4 py-12">
      <section className="w-full rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
        <h1 className="text-2xl font-bold text-white">Secure checkout</h1>
        <p className="mt-2 text-slate-300">Sign in before continuing to the secure payment provider.</p>
        <div className="mt-6">
          <GeneratedCheckoutButton className="rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-60" />
        </div>
        <p className="mt-4 text-sm text-slate-400">
          Need an account? <Link className="underline" to="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
""",
                    encoding="utf-8",
                )
                created.append("frontend/src/pages/GeneratedCheckoutPage.jsx")

            payment_success_page = pages / "GeneratedPaymentSuccess.jsx"
            if not payment_success_page.is_file():
                payment_success_page.write_text(
                    """import React, { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

export default function GeneratedPaymentSuccess() {
  const [params] = useSearchParams();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const orderId = params.get('order_id');

  const loadOrderStatus = useCallback(async () => {
    setError('');
    if (!orderId) {
      setError('The order reference is missing.');
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/payments/orders/${encodeURIComponent(orderId)}`, {
        credentials: 'include',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const result = await response.json();
      if (!response.ok || !result.success) {
        throw new Error(result.message || 'Order status could not be verified.');
      }
      setOrder(result.data);
    } catch (statusError) {
      setError(statusError.message || 'Order status could not be verified.');
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => { loadOrderStatus(); }, [loadOrderStatus]);

  return (
    <main className="mx-auto min-h-[60vh] w-full max-w-xl px-4 py-16">
      <section aria-live="polite" className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        {loading && <p>Checking payment status…</p>}
        {!loading && error && <p role="alert">{error}</p>}
        {!loading && order?.status === 'paid' && <h1 className="text-2xl font-bold">Payment confirmed</h1>}
        {!loading && order && order.status !== 'paid' && (
          <p role="status">Payment status: {order.status}. Confirmation may take a moment.</p>
        )}
        {!loading && <button type="button" className="mt-4 underline" onClick={loadOrderStatus}>Check again</button>}
        <p className="mt-4"><Link to="/register">Create an account</Link> · <Link to="/">Return to the website</Link></p>
      </section>
    </main>
  );
}
""",
                    encoding="utf-8",
                )
                created.append("frontend/src/pages/GeneratedPaymentSuccess.jsx")

            app_file = frontend_src / "App.jsx"
            if not app_file.is_file():
                raise ValueError("Cannot wire Stripe checkout without frontend/src/App.jsx.")
            app_source = app_file.read_text(encoding="utf-8")
            if "<Routes" not in app_source or "</Routes>" not in app_source:
                raise ValueError("Cannot wire Stripe checkout: App.jsx must expose a React Router Routes block.")
            route_specs = (
                ("/checkout", "GeneratedCheckoutPage"),
                ("/payment/success", "GeneratedPaymentSuccess"),
            )
            for route_path, component in route_specs:
                import_line = (
                    f"import {component} from './pages/{component}.jsx';"
                )
                if component not in app_source:
                    existing_imports = list(re.finditer(r"(?m)^import\s+[^\n;]+;\s*$", app_source))
                    if existing_imports:
                        index = existing_imports[-1].end()
                        app_source = app_source[:index] + "\n" + import_line + app_source[index:]
                    else:
                        app_source = import_line + "\n" + app_source
                route_pattern = re.compile(
                    rf"""<Route\b[^>]*path\s*=\s*['"]{re.escape(route_path)}['"]"""
                )
                if not route_pattern.search(app_source):
                    route_close = app_source.rfind("</Routes>")
                    app_source = (
                        app_source[:route_close]
                        + f'<Route path="{route_path}" element={{<{component} />}} />\n'
                        + app_source[route_close:]
                    )
            app_file.write_text(app_source, encoding="utf-8")
            created.append("frontend/src/App.jsx (checkout routes wired)")

        readme = backend / "README.md"
        current_readme = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        if "Payments (Stripe Checkout)" not in current_readme:
            readme.write_text(current_readme.rstrip() + "\n" + _README_SECTION, encoding="utf-8")
        agent_logger.info("Generated explicit Stripe checkout scaffolding.")
        return {
            "status": "ok",
            "created": created,
            "note": "Configure Stripe credentials and a Stripe Price ID before checkout is enabled.",
            "endpoints": [
                "POST /api/payments/checkout-session",
                "POST /api/payments/webhook",
            ],
        }


def scaffold_checkout(project_dir: str) -> Dict[str, Any]:
    return CheckoutScaffolder(project_dir).scaffold()
