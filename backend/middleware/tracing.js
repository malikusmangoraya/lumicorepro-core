/**
 * Distributed tracing — W3C Trace Context (traceparent) propagation.
 * -------------------------------------------------------------------
 * A request's trace ID travels: browser (axios interceptor) → Express →
 * FastAPI AI agent. No vendor SDK required — we implement the W3C header
 * format directly and use node's AsyncLocalStorage so any downstream
 * fetch to the agent picks up the parent context automatically.
 *
 *   traceparent: 00-<32hex trace-id>-<16hex span-id>-01
 *
 * Response header `X-Trace-Id` lets support map a user complaint to the
 * exact request across every hop and log line.
 */
import { AsyncLocalStorage } from 'node:async_hooks';
import crypto from 'node:crypto';

const als = new AsyncLocalStorage();

const TRACEPARENT_RE = /^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/;

export function newSpanId() {
  return crypto.randomBytes(8).toString('hex');
}

export function newTraceId() {
  return crypto.randomBytes(16).toString('hex');
}

/** Serialize a traceparent header value from ids. */
export function formatTraceparent(traceId, spanId, flags = '01') {
  return `00-${traceId}-${spanId}-${flags}`;
}

/** Parse a traceparent header; returns { traceId, spanId, flags } or null. */
export function parseTraceparent(value) {
  if (typeof value !== 'string') return null;
  const m = TRACEPARENT_RE.exec(value.trim().toLowerCase());
  if (!m) return null;
  return { traceId: m[1], spanId: m[2], flags: m[3] };
}

/** Context of the current request, if any. */
export function currentTraceContext() {
  return als.getStore() || null;
}

/**
 * Headers that must be attached to every downstream (AI agent) call so the
 * trace continues across services. Safe to call anywhere inside a request.
 */
export function downstreamTraceHeaders() {
  const ctx = als.getStore();
  if (!ctx) return {};
  // Each hop is its own span: new span id, same trace id.
  return { traceparent: formatTraceparent(ctx.traceId, newSpanId()), 'x-trace-id': ctx.traceId };
}

/**
 * Express middleware. Extracts an incoming traceparent (or starts one),
 * opens an AsyncLocalStorage scope for the whole request and stamps the
 * response with X-Trace-Id.
 */
export function tracingMiddleware(req, res, next) {
  const incoming = parseTraceparent(req.headers['traceparent']);
  const traceId = incoming?.traceId || newTraceId();
  const spanId = newSpanId();
  const startedAt = process.hrtime.bigint();

  const store = {
    traceId,
    spanId,
    parentSpanId: incoming?.spanId || null,
    requestId: req.id || traceId.slice(0, 16),
    startedAt,
  };

  res.setHeader('X-Trace-Id', traceId);
  req.traceId = traceId;
  req.traceparent = formatTraceparent(traceId, spanId);
  if (!incoming) {
    // First hop in the chain — tell upstream clients how to continue it.
    res.setHeader('traceparent', formatTraceparent(traceId, spanId));
  }

  als.run(store, () => next());
}

export default { tracingMiddleware, downstreamTraceHeaders, currentTraceContext, parseTraceparent, formatTraceparent };
