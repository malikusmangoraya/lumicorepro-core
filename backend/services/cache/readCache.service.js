/**
 * Read-through cache for heavy dashboard/analytics reads.
 * --------------------------------------------------------
 * Heavy admin endpoints (revenue reports, KPI dashboards) were hitting the
 * primary Postgres on every dashboard refresh. This wrapper caches their JSON
 * in Redis (multi-worker safe) with:
 *   - TTL jitter (±10%) so a mass of keys never expire simultaneously;
 *   - a single-flight promise map so N concurrent misses trigger ONE query;
 *   - a tiny in-memory fallback when Redis is down (bounded by max entries);
 *   - `invalidate(prefix)` for write paths (order/payment mutations).
 *
 * Usage:  const data = await cachedRead(`analytics:revenue:${orgId}`, 60, () =>
 *           analyticsService.revenueReport({ days, orgId }));
 */
import { getRedis, isRedisAvailable } from './redis.client.js';
import logger from '../../utils/logger.js';

const DEFAULT_TTL = 60;
const MAX_MEMORY_ENTRIES = 200;
const memory = new Map(); // key -> { expiresAt, value }
const inflight = new Map(); // key -> Promise

function jitteredTtl(ttlSeconds) {
  const jitter = ttlSeconds * 0.1;
  return Math.max(1, Math.round(ttlSeconds + (Math.random() * 2 - 1) * jitter));
}

function memoryGet(key) {
  const hit = memory.get(key);
  if (!hit) return undefined;
  if (hit.expiresAt < Date.now()) {
    memory.delete(key);
    return undefined;
  }
  return hit.value;
}

function memorySet(key, value, ttlSeconds) {
  if (memory.size >= MAX_MEMORY_ENTRIES) {
    const oldest = memory.keys().next().value;
    memory.delete(oldest);
  }
  memory.set(key, { expiresAt: Date.now() + ttlSeconds * 1000, value });
}

/**
 * Cache `fn()`'s JSON result under `key` for `ttlSeconds`.
 * Never throws: on any cache/DB failure the error from `fn()` propagates
 * (callers already have try/catch), but cache-layer errors are swallowed.
 */
export async function cachedRead(key, ttlSeconds, fn) {
  const ttl = Number(ttlSeconds) > 0 ? Number(ttlSeconds) : DEFAULT_TTL;

  // 1. Fast path — Redis, then memory.
  if (isRedisAvailable()) {
    try {
      const raw = await getRedis().get(`rc:${key}`);
      if (raw) return JSON.parse(raw);
    } catch { /* fall through to memory */ }
  }
  const memHit = memoryGet(key);
  if (memHit !== undefined) return memHit;

  // 2. Single flight — coalesce concurrent misses into one underlying call.
  if (inflight.has(key)) return inflight.get(key);
  const promise = (async () => {
    try {
      const value = await fn();
      const ttlJ = jitteredTtl(ttl);
      if (isRedisAvailable()) {
        try {
          await getRedis().set(`rc:${key}`, JSON.stringify(value), 'EX', ttlJ);
        } catch { /* memory still covers this process */ }
      }
      memorySet(key, value, ttlJ);
      return value;
    } finally {
      inflight.delete(key);
    }
  })();
  inflight.set(key, promise);
  return promise;
}

/** Drop cached reads — call from write paths (orders, payments, products). */
export async function invalidateReadCache(prefix) {
  let removedMemory = 0;
  for (const key of [...memory.keys()]) {
    if (!prefix || key.startsWith(prefix)) {
      memory.delete(key);
      removedMemory += 1;
    }
  }
  if (isRedisAvailable() && prefix) {
    try {
      const r = getRedis();
      // SCAN (non-blocking) + delete in batches.
      let cursor = '0';
      do {
        const [next, keys] = await r.scan(cursor, 'MATCH', `rc:${prefix}*`, 'COUNT', 200);
        cursor = next;
        if (keys.length) await r.del(...keys);
      } while (cursor !== '0');
    } catch (err) {
      logger.warn(`Read-cache invalidation incomplete: ${err.message}`);
    }
  }
  return { removedMemory };
}

export function cacheStats() {
  return { memoryEntries: memory.size, inflight: inflight.size, redis: isRedisAvailable() };
}

export default { cachedRead, invalidateReadCache, cacheStats };
