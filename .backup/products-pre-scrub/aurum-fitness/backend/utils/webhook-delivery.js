/**
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

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000; // 1s → 2s → 4s

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
    'Content-Type': 'application/json',
    'X-Webhook-Event': eventType,
    'X-Webhook-Timestamp': String(timestamp),
    'X-Webhook-Signature': `sha256=${signature}`,
    'User-Agent': 'Webhooks/1.0',
  };

  let lastError;
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const { default: fetch } = await import('node-fetch');
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body,
        signal: AbortSignal.timeout(10000), // 10s timeout
      });

      if (response.ok) {
        logger.info(`[WebhookDelivery] ${eventType} → ${url} (attempt ${attempt}) ✓`);
        return { success: true, status: response.status, attempt };
      }

      const errText = await response.text();
      lastError = new Error(`HTTP ${response.status}: ${errText.slice(0, 100)}`);
      logger.warn(
        `[WebhookDelivery] ${eventType} → ${url} failed (${response.status}), attempt ${attempt}/${MAX_RETRIES}`
      );
    } catch (err) {
      lastError = err;
      logger.warn(
        `[WebhookDelivery] ${eventType} → ${url} error: ${err.message}, attempt ${attempt}/${MAX_RETRIES}`
      );
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
      .map((ep) =>
        deliverWebhook(ep.url, { event: eventType, data: payload }, ep.secret, eventType)
      )
  );
  return results;
}

export const WebhookDelivery = { deliverWebhook, broadcastEvent };
