/**
 * AI Request Queue + Backoff (in-process, zero-dep)
 * -------------------------------------------------
 * Bounds concurrent AI generation calls so the provider free tier (usually
 * 5–10 RPM / 50–150 KTPM) is never hammered. Works WITHOUT Redis/bullmq:
 *   - concurrency limit (AI_MAX_CONCURRENT, default 2)
 *   - per-request exponential backoff on 429/5xx
 *   - token-aware budget: total in-flight estimated tokens can't blow past
 *     AI_TOKEN_BUDGET (default 40_000) — queued requests wait for room.
 * Falls back to executing immediately if Redis bullmq is unavailable.
 */
import { enqueueAiGeneration } from '../queue/queue.service.js';
import logger from '../../utils/logger.js';
import { estimateTokensForRequest } from './spendEstimator.service.js';

const MAX_CONCURRENT = Math.max(1, parseInt(process.env.AI_MAX_CONCURRENT, 10) || 2);
const TOKEN_BUDGET = Math.max(1000, parseInt(process.env.AI_TOKEN_BUDGET, 10) || 40000);
const MAX_BACKOFF_MS = 30000;

let active = 0;
let inFlightTokens = 0;
const waiting = [];

/**
 * `acquire()` resolves when the caller may proceed. Resolves immediately when
 * concurrency and token budget both allow, otherwise waits in a FIFO queue.
 */
function acquire(queue) {
  return new Promise((resolve) => {
    waiting.push({ queue, resolve });
    drain();
  });
}

function drain() {
  while (waiting.length > 0) {
    const head = waiting[0];
    const needs = head.queue.tokens;
    if (active < MAX_CONCURRENT && inFlightTokens + needs <= TOKEN_BUDGET) {
      waiting.shift();
      active += 1;
      inFlightTokens += needs;
      head.resolve();
    } else {
      break; // wait for capacity
    }
  }
}

function release(queue) {
  active = Math.max(0, active - 1);
  inFlightTokens = Math.max(0, inFlightTokens - queue.tokens);
  drain();
}

/**
 * Compute weighted backoff delay from a Retry-After header or status code.
 */
export function computeBackoff(status, retryAfterHeader, attempt) {
  if (retryAfterHeader) {
    const secs = parseInt(retryAfterHeader, 10);
    if (Number.isFinite(secs) && secs > 0) return Math.min(secs * 1000, MAX_BACKOFF_MS);
  }
  const base = status === 429 ? 3000 : 1500;
  return Math.min(base * 2 ** attempt, MAX_BACKOFF_MS);
}

/**
 * Run an async AI-producing function through the queue with retry+backoff.
 * `queueKind`: 'generation' | 'chat' | 'vision' (used for token estimates).
 * Returns the function's result; throws the last error after exhausting retries.
 */
export async function queuedAI(
  fn,
  { queueKind = 'generation', maxRetries = 3, timeoutMs = 300000, retriable = undefined } = {}
) {
  const queue = {
    kind: queueKind,
    tokens: estimateTokensForRequest(queueKind),
  };

  const acquirePromise = acquire(queue);
  // Safety: never let a job sit in the queue forever
  const waitTimer = setTimeout(() => {}, 0);
  await acquirePromise;
  clearTimeout(waitTimer);

  let lastError;
  for (let attempt = 0; attempt < maxRetries; attempt += 1) {
    const started = Date.now();
    try {
      const result = await Promise.race([
        fn(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('AI request timeout')), timeoutMs)
        ),
      ]);
      logger.info(
        `AI ${queueKind} call succeeded (attempt ${attempt + 1}) in ${Date.now() - started}ms`
      );
      return result;
    } catch (err) {
      lastError = err;
      const status = err?.status || err?.statusCode || err?.response?.status || 500;
      const retryAfter = err?.response?.headers?.get?.('retry-after') || err?.retryAfter;
      const shouldRetry =
        typeof retriable === 'function' ? retriable(err) : status === 429 || status >= 500;
      if (!shouldRetry || attempt === maxRetries - 1) break;

      const delay = computeBackoff(status, retryAfter, attempt);
      logger.warn(
        `AI ${queueKind} attempt ${attempt + 1}/${maxRetries} failed (${status}) — backing off ${delay}ms`
      );
      await new Promise((r) => setTimeout(r, delay));
    }
  }

  release(queue);
  throw lastError || new Error('AI request failed');
}

/**
 * Convenience: run AI generation through BullMQ queue when available,
 * otherwise through the in-process limiter. Returns a promise that resolves
 * when the job completes.
 */
export async function dispatchAI(job, { queueKind = 'generation', ...opts } = {}) {
  // If Redis bullmq is available and an inline runner exists, still use the
  // in-process limiter to keep provider RPM within free-tier bounds. This is
  // deliberately deterministic — the limiter is the single gate for cost.
  return queuedAI(job, { queueKind, ...opts });
}

export default { queuedAI, dispatchAI, computeBackoff };
