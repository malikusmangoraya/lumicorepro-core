"""
Webhook Manager — LumicorePro AI Agent
=======================================
Phase 14 — Global Integrations

Generates production-ready webhook infrastructure:
  - Webhook registry (which events to expose per website type)
  - Express webhook router with HMAC-SHA256 signature verification
  - Event bus (EventEmitter pattern for internal event routing)
  - Retry queue with exponential backoff
  - Webhook delivery log (SQLite)
  - Dead letter queue handling
  - Supported: Stripe, GitHub, Shopify, Slack, Discord, custom webhooks
  - WEBHOOKS.md integration guide
"""

import os
import json
from typing import Dict, Any, List
from utils.logger import agent_logger


class WebhookManager:
    """Webhook infrastructure generator for global integrations."""

    # ── Webhook event registry per website type ───────────────────────────
    WEBHOOK_EVENTS: Dict[str, List[Dict[str, Any]]] = {
        "ecommerce": [
            {"event": "order.created",           "source": "internal", "description": "New order placed"},
            {"event": "order.paid",              "source": "stripe",   "description": "Stripe payment succeeded"},
            {"event": "order.shipped",           "source": "internal", "description": "Order marked as shipped"},
            {"event": "order.delivered",         "source": "internal", "description": "Order delivered"},
            {"event": "order.cancelled",         "source": "internal", "description": "Order cancelled"},
            {"event": "order.refunded",          "source": "stripe",   "description": "Stripe refund processed"},
            {"event": "payment.failed",          "source": "stripe",   "description": "Stripe payment failed"},
            {"event": "subscription.created",    "source": "stripe",   "description": "New subscription"},
            {"event": "subscription.cancelled",  "source": "stripe",   "description": "Subscription cancelled"},
            {"event": "inventory.low",           "source": "internal", "description": "Stock below threshold"},
            {"event": "review.submitted",        "source": "internal", "description": "Customer review submitted"},
            {"event": "user.registered",         "source": "internal", "description": "New user signup"},
        ],
        "saas": [
            {"event": "subscription.created",   "source": "stripe",   "description": "New subscription"},
            {"event": "subscription.upgraded",  "source": "stripe",   "description": "Plan upgraded"},
            {"event": "subscription.downgraded","source": "stripe",   "description": "Plan downgraded"},
            {"event": "subscription.cancelled", "source": "stripe",   "description": "Subscription cancelled"},
            {"event": "invoice.paid",           "source": "stripe",   "description": "Invoice payment succeeded"},
            {"event": "invoice.failed",         "source": "stripe",   "description": "Invoice payment failed"},
            {"event": "user.registered",        "source": "internal", "description": "New user signup"},
            {"event": "user.trial_started",     "source": "internal", "description": "Trial period started"},
            {"event": "user.trial_expiring",    "source": "internal", "description": "Trial ending in 3 days"},
            {"event": "feature.limit_reached",  "source": "internal", "description": "Usage limit hit"},
        ],
        "healthcare": [
            {"event": "appointment.booked",     "source": "internal", "description": "New appointment booked"},
            {"event": "appointment.confirmed",  "source": "internal", "description": "Appointment confirmed"},
            {"event": "appointment.cancelled",  "source": "internal", "description": "Appointment cancelled"},
            {"event": "appointment.reminder",   "source": "internal", "description": "24h reminder sent"},
            {"event": "prescription.created",   "source": "internal", "description": "Prescription issued"},
            {"event": "payment.received",       "source": "stripe",   "description": "Payment received"},
        ],
        "restaurant": [
            {"event": "order.placed",           "source": "internal", "description": "Online order placed"},
            {"event": "order.confirmed",        "source": "internal", "description": "Order confirmed by kitchen"},
            {"event": "order.ready",            "source": "internal", "description": "Order ready for pickup"},
            {"event": "order.delivered",        "source": "internal", "description": "Delivery completed"},
            {"event": "reservation.created",    "source": "internal", "description": "Table reservation made"},
            {"event": "reservation.cancelled",  "source": "internal", "description": "Reservation cancelled"},
            {"event": "payment.received",       "source": "stripe",   "description": "Online payment received"},
        ],
        "default": [
            {"event": "user.registered",        "source": "internal", "description": "New user registration"},
            {"event": "contact.submitted",      "source": "internal", "description": "Contact form submitted"},
            {"event": "payment.received",       "source": "stripe",   "description": "Payment received"},
            {"event": "newsletter.subscribed",  "source": "internal", "description": "Newsletter signup"},
        ],
    }

    # ── Outbound integrations ─────────────────────────────────────────────
    INTEGRATIONS: Dict[str, Dict[str, Any]] = {
        "slack":    {"event_trigger": "order.created, payment.failed", "method": "POST", "auth": "webhook_url"},
        "discord":  {"event_trigger": "order.created",                 "method": "POST", "auth": "webhook_url"},
        "mailchimp":{"event_trigger": "user.registered",               "method": "POST", "auth": "api_key"},
        "zapier":   {"event_trigger": "*",                             "method": "POST", "auth": "webhook_url"},
        "n8n":      {"event_trigger": "*",                             "method": "POST", "auth": "webhook_url"},
        "make":     {"event_trigger": "*",                             "method": "POST", "auth": "webhook_url"},
        "stripe":   {"event_trigger": "payment.*",                     "method": "POST", "auth": "stripe_signature"},
    }

    def generate(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        """Generate webhook infrastructure code."""
        agent_logger.info("WebhookManager: Generating webhook infrastructure...")

        website_type = spec.get("website_type", "default")
        events = self.WEBHOOK_EVENTS.get(website_type, self.WEBHOOK_EVENTS["default"])

        artifacts = []
        backend = os.path.join(project_dir, "backend")
        routes_dir  = os.path.join(backend, "routes")
        utils_dir   = os.path.join(backend, "utils")
        models_dir  = os.path.join(backend, "models")
        os.makedirs(routes_dir, exist_ok=True)
        os.makedirs(utils_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)

        # 1. webhook-registry.json
        reg_path = os.path.join(backend, "webhook-registry.json")
        self._write(reg_path, json.dumps(
            {"events": events, "integrations": list(self.INTEGRATIONS.keys())},
            indent=2
        ))
        artifacts.append(reg_path)

        # 2. webhook.routes.js — Express router
        routes_path = os.path.join(routes_dir, "webhook.routes.js")
        self._write(routes_path, self._build_routes(events))
        artifacts.append(routes_path)

        # 3. event-bus.js — Internal event emitter
        bus_path = os.path.join(utils_dir, "event-bus.js")
        self._write(bus_path, self._build_event_bus(events))
        artifacts.append(bus_path)

        # 4. webhook-delivery.js — Outbound webhook delivery with retry
        delivery_path = os.path.join(utils_dir, "webhook-delivery.js")
        self._write(delivery_path, self._build_delivery())
        artifacts.append(delivery_path)

        # 5. WebhookLog.js — Mongoose model for delivery log
        model_path = os.path.join(models_dir, "WebhookLog.js")
        self._write(model_path, self._build_model())
        artifacts.append(model_path)

        # 6. WEBHOOKS.md
        md_path = os.path.join(project_dir, "WEBHOOKS.md")
        self._write(md_path, self._build_md(events, website_type))
        artifacts.append(md_path)

        result = {
            "events_registered": len(events),
          "total_events":     len(events),
            "integrations":      list(self.INTEGRATIONS.keys()),
            "artifacts":         artifacts,
            "stripe_events":     [e["event"] for e in events if e["source"] == "stripe"],
            "internal_events":   [e["event"] for e in events if e["source"] == "internal"],
        }
        agent_logger.info(
            f"WebhookManager: {len(events)} events, "
            f"{len(self.INTEGRATIONS)} integrations."
        )
        return result

    def _build_routes(self, events):
        event_list = json.dumps([e["event"] for e in events], indent=4)
        return f"""/**
 * Webhook Routes — Auto-generated for internal event handling
 * Handles inbound webhooks from Stripe and other providers
 * Emits internal events via EventBus for all downstream processing
 */

import express from 'express';
import crypto from 'crypto';
import Stripe from 'stripe';
import {{ eventBus }} from '../utils/event-bus.js';
import {{ WebhookDelivery }} from '../utils/webhook-delivery.js';
import WebhookLog from '../models/WebhookLog.js';
import logger from '../utils/logger.js';

const router = express.Router();
const stripe = process.env.STRIPE_SECRET_KEY ? new Stripe(process.env.STRIPE_SECRET_KEY) : null;

// ── Registered internal events ──────────────────────────────────────────
export const REGISTERED_EVENTS = {event_list};

// ── HMAC-SHA256 Signature Verification ──────────────────────────────────
function verifySignature(payload, signature, secret) {{
  if (!secret || !signature) return false;
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  // Constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(signature, 'hex'),
    Buffer.from(expected, 'hex')
  );
}}

/**
 * POST /api/webhooks/stripe
 * Stripe webhook endpoint — raw body required for signature verification
 */
router.post('/stripe', express.raw({{ type: 'application/json' }}), async (req, res) => {{
  const sig = req.headers['stripe-signature'];
  const secret = process.env.STRIPE_WEBHOOK_SECRET;

  let event;
  try {{
    if (stripe && secret && sig) {{
      event = stripe.webhooks.constructEvent(req.body, sig, secret);
    }} else {{
      event = JSON.parse(req.body.toString());
    }}
  }} catch (err) {{
    logger.error(`Stripe webhook signature failed: ${{err.message}}`);
    return res.status(400).json({{ error: `Webhook Error: ${{err.message}}` }});
  }}

  // Log the delivery
  await WebhookLog.create({{
    source: 'stripe',
    event: event.type,
    payload: JSON.stringify(event),
    status: 'received',
  }}).catch(() => {{}});

  // Emit to internal event bus
  const internalEvent = `stripe.${{event.type}}`;
  eventBus.emit(internalEvent, event.data.object);
  eventBus.emit('stripe.*', {{ type: event.type, data: event.data.object }});

  logger.info(`Stripe webhook: ${{event.type}}`);
  res.json({{ received: true }});
}});

/**
 * POST /api/webhooks/custom
 * Generic inbound webhook endpoint with HMAC signature verification
 * Consumers register endpoints via the webhook registry
 */
router.post('/custom/:source', express.json(), async (req, res) => {{
  const {{ source }} = req.params;
  const signature = req.headers['x-webhook-signature'] || req.headers['x-hub-signature-256'];
  const secret = process.env[`WEBHOOK_SECRET_${{source.toUpperCase()}}`];

  if (secret && signature) {{
    const rawBody = JSON.stringify(req.body);
    const isValid = verifySignature(rawBody, signature.replace('sha256=', ''), secret);
    if (!isValid) {{
      logger.warn(`Invalid webhook signature for source: ${{source}}`);
      return res.status(401).json({{ error: 'Invalid signature' }});
    }}
  }}

  const eventType = req.headers['x-webhook-event'] || req.body.event || 'unknown';
  await WebhookLog.create({{
    source,
    event: eventType,
    payload: JSON.stringify(req.body),
    status: 'received',
  }}).catch(() => {{}});

  eventBus.emit(`${{source}}.${{eventType}}`, req.body);
  logger.info(`Custom webhook: ${{source}}/${{eventType}}`);
  res.json({{ received: true }});
}});

/**
 * POST /api/webhooks/emit
 * Internal endpoint to trigger events programmatically (authenticated)
 * Used by backend services to fire events for downstream processing
 */
router.post('/emit', async (req, res, next) => {{
  try {{
    const {{ event, data, secret }} = req.body;
    if (!event) return res.status(400).json({{ error: 'event is required' }});

    // Optional internal secret check
    const internalSecret = process.env.INTERNAL_WEBHOOK_SECRET;
    if (internalSecret && secret !== internalSecret) {{
      return res.status(401).json({{ error: 'Unauthorized' }});
    }}

    if (!REGISTERED_EVENTS.includes(event)) {{
      return res.status(400).json({{ error: `Unknown event: ${{event}}. See WEBHOOKS.md` }});
    }}

    eventBus.emit(event, data || {{}});
    await WebhookLog.create({{ source: 'internal', event, payload: JSON.stringify(data), status: 'emitted' }}).catch(() => {{}});

    logger.info(`Internal event emitted: ${{event}}`);
    res.json({{ success: true, event }});
  }} catch (err) {{
    next(err);
  }}
}});

/**
 * GET /api/webhooks/logs
 * Return recent webhook delivery logs (admin only in production)
 */
router.get('/logs', async (req, res, next) => {{
  try {{
    const limit = Math.min(parseInt(req.query.limit || '50'), 200);
    const logs = await WebhookLog.find({{}}).sort({{ createdAt: -1 }}).limit(limit);
    res.json({{ logs }});
  }} catch (err) {{
    next(err);
  }}
}});

export default router;
"""

    def _build_event_bus(self, events):
        handlers = "\n".join(
            f"  // eventBus.on('{e['event']}', async (data) => {{ /* handle */ }});"
            for e in events[:6]
        )
        return f"""/**
 * Event Bus — Internal EventEmitter for the application
 * Auto-generated for internal event handling
 *
 * Usage:
 *   import {{ eventBus }} from './event-bus.js';
 *   eventBus.emit('order.created', {{ orderId: '...' }});
 *   eventBus.on('order.created', async (data) => {{ ... }});
 */

import {{ EventEmitter }} from 'events';
import logger from './logger.js';

class LumicoreEventBus extends EventEmitter {{
  constructor() {{
    super();
    this.setMaxListeners(50);  // Increase for many subscribers
    this._stats = {{}};
  }}

  emit(event, ...args) {{
    this._stats[event] = (this._stats[event] || 0) + 1;
    logger.debug(`[EventBus] ${{event}} (total: ${{this._stats[event]}})`);
    return super.emit(event, ...args);
  }}

  on(event, listener) {{
    logger.debug(`[EventBus] Registered listener: ${{event}}`);
    return super.on(event, async (...args) => {{
      try {{
        await listener(...args);
      }} catch (err) {{
        logger.error(`[EventBus] Error in listener for ${{event}}: ${{err.message}}`);
      }}
    }});
  }}

  getStats() {{
    return {{ ...this._stats }};
  }}
}}

export const eventBus = new LumicoreEventBus();

// ── Register default handlers ────────────────────────────────────────────
// Uncomment and implement the handlers you need:
{handlers}

export default eventBus;
"""

    def _build_delivery(self):
        return """/**
 * Webhook Delivery — Outbound webhook sender with retry
 *
 * Supports:
 *   - HMAC-SHA256 signature on all outbound webhooks
 *   - Exponential backoff retry (3 attempts)
 *   - Dead letter queue logging on final failure
 *   - Configurable timeout per endpoint
 */

import crypto from 'crypto';
import logger from './logger.js';

const MAX_RETRIES   = 3;
const BASE_DELAY_MS = 1000;  // 1s → 2s → 4s

/**
 * Deliver a webhook payload to an endpoint with retries
 * @param {string} url        - Target endpoint URL
 * @param {object} payload    - Event payload to send
 * @param {string} secret     - HMAC secret for signature
 * @param {string} eventType  - Event type header
 */
export async function deliverWebhook(url, payload, secret = '', eventType = 'event') {
  const body = JSON.stringify(payload);
  const timestamp = Math.floor(Date.now() / 1000);

  const signature = secret
    ? crypto.createHmac('sha256', secret).update(`${timestamp}.${body}`).digest('hex')
    : '';

  const headers = {
    'Content-Type':       'application/json',
    'X-Webhook-Event':    eventType,
    'X-Webhook-Timestamp':String(timestamp),
    'X-Webhook-Signature':`sha256=${signature}`,
    'User-Agent':         'Webhooks/1.0',
  };

  let lastError;
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const { default: fetch } = await import('node-fetch');
      const response = await fetch(url, {
        method:  'POST',
        headers,
        body,
        signal:  AbortSignal.timeout(10000),  // 10s timeout
      });

      if (response.ok) {
        logger.info(`[WebhookDelivery] ${eventType} → ${url} (attempt ${attempt}) ✓`);
        return { success: true, status: response.status, attempt };
      }

      const errText = await response.text();
      lastError = new Error(`HTTP ${response.status}: ${errText.slice(0, 100)}`);
      logger.warn(`[WebhookDelivery] ${eventType} → ${url} failed (${response.status}), attempt ${attempt}/${MAX_RETRIES}`);
    } catch (err) {
      lastError = err;
      logger.warn(`[WebhookDelivery] ${eventType} → ${url} error: ${err.message}, attempt ${attempt}/${MAX_RETRIES}`);
    }

    if (attempt < MAX_RETRIES) {
      await new Promise((r) => setTimeout(r, BASE_DELAY_MS * 2 ** (attempt - 1)));
    }
  }

  // Dead letter queue — log final failure
  logger.error(`[WebhookDelivery] DEAD LETTER: ${eventType} → ${url}: ${lastError?.message}`);
  return { success: false, error: lastError?.message, attempt: MAX_RETRIES };
}

/**
 * Send webhook to all registered endpoints for an event
 * Endpoint list comes from WEBHOOK_ENDPOINTS env var (JSON array)
 */
export async function broadcastEvent(eventType, payload) {
  const endpoints = JSON.parse(process.env.WEBHOOK_ENDPOINTS || '[]');
  const results = await Promise.allSettled(
    endpoints
      .filter((ep) => ep.events.includes('*') || ep.events.includes(eventType))
      .map((ep) => deliverWebhook(ep.url, { event: eventType, data: payload }, ep.secret, eventType))
  );
  return results;
}

export const WebhookDelivery = { deliverWebhook, broadcastEvent };
"""

    def _build_model(self):
        return """/**
 * WebhookLog — Mongoose Model for webhook delivery audit trail
 */

import mongoose from 'mongoose';

const webhookLogSchema = new mongoose.Schema({
  source:    { type: String, required: true, index: true },
  event:     { type: String, required: true, index: true },
  payload:   { type: String },
  status:    { type: String, enum: ['received', 'emitted', 'delivered', 'failed', 'dead_letter'], default: 'received' },
  attempts:  { type: Number, default: 0 },
  error:     { type: String },
  createdAt: { type: Date, default: Date.now, index: true, expires: 2592000 }, // TTL 30 days
});

webhookLogSchema.index({ source: 1, event: 1, createdAt: -1 });

export default mongoose.model('WebhookLog', webhookLogSchema);
"""

    def _build_md(self, events, website_type):
        lines = [
            f"# Webhook Integration Guide — {website_type.title()}",
            "\n## Inbound Endpoints\n",
            "| Endpoint | Source | Description |",
            "|----------|--------|-------------|",
            "| `POST /api/webhooks/stripe` | Stripe | Payment events |",
            "| `POST /api/webhooks/custom/:source` | Any | Generic HMAC-signed webhooks |",
            "| `POST /api/webhooks/emit` | Internal | Programmatic event emission |",
            "| `GET /api/webhooks/logs` | Internal | Delivery audit log |",
            "\n## Registered Events\n",
            "| Event | Source | Description |",
            "|-------|--------|-------------|",
        ]
        for e in events:
            lines.append(f"| `{e['event']}` | {e['source']} | {e['description']} |")
        lines += [
            "\n## Environment Variables\n```bash",
            "STRIPE_WEBHOOK_SECRET=whsec_xxx  # From Stripe Dashboard",
            "INTERNAL_WEBHOOK_SECRET=your_secret",
            'WEBHOOK_ENDPOINTS=\'[{"url":"https://hooks.slack.com/xxx","events":["order.created"],"secret":"xxx"}]\'',
            "```",
            "\n## Usage Example\n```javascript",
            "import { eventBus } from './utils/event-bus.js';",
            "",
            "// Emit an event after order is created:",
            "eventBus.emit('order.created', { orderId: order._id, total: order.total });",
            "",
            "// Listen for an event:",
            "eventBus.on('order.created', async (data) => {",
            "  await sendOrderConfirmationEmail(data.orderId);",
            "  await notifySlack(data);",
            "});",
            "```",
        ]
        return "\n".join(lines)

    def _write(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            agent_logger.warning(f"WebhookManager: Could not write {path}: {e}")
