/**
 * Cache Service (Redis-backed with in-memory fallback)
 * ----------------------------------------------------
 * High-level get/set/invalidate wrapper around the Redis client used for
 * expensive/repeated DB reads (dashboard stats, product listings, search).
 * Falls back to an in-memory Map when Redis is unavailable (works offline).
 */
import { getRedis, isRedisAvailable } from './redis.client.js';

const TTL = {
  SHORT: 60, // 1 min
  MEDIUM: 300, // 5 min (dashboard stats)
  LONG: 3600, // 1 hr (reference data)
  PRODUCT_LIST: 300,
  SEARCH: 600,
  DASHBOARD: 120,
};

function keyFor(...parts) {
  return `cache:${parts.map((p) => String(p).replace(/[^a-zA-Z0-9_.:-]/g, '_')).join(':')}`;
}

const cache = {
  TTL,

  isAvailable() {
    return isRedisAvailable();
  },

  /** Get a JSON value (returns undefined on miss). */
  async get(namespace, key) {
    const full = keyFor(namespace, key);
    const raw = await getRedis().get(full);
    if (raw == null) return undefined;
    try {
      return JSON.parse(raw);
    } catch {
      // Not JSON — stored as a plain string, return it as-is
      return raw;
    }
  },

  /** Store a JSON value with TTL in seconds. */
  async set(namespace, key, value, ttl = TTL.MEDIUM) {
    const full = keyFor(namespace, key);
    const serialized = typeof value === 'string' ? value : JSON.stringify(value);
    await getRedis().set(full, serialized, 'EX', ttl);
    return true;
  },

  /** Invalidate exact keys under any namespaces. */
  async invalidate(...keys) {
    const full = keys.map((k) => keyFor('*', k) /* unused */);
    // keys passed are fully-qualified cache keys when they include '::'
    const targets = keys
      .flatMap((k) => {
        if (k.includes('::')) return [k];
        return [k];
      })
      .filter(Boolean);
    const del = await getRedis().del(...targets);
    return del > 0;
  },

  /** Invalidate all keys matching a namespace prefix (e.g. 'products'). */
  async invalidateNamespace(namespace, pattern = '*') {
    const nsPrefix = keyFor(namespace, '');
    const raw = await getRedis().keys(`${nsPrefix}*`);
    if (raw.length) await getRedis().del(...raw);
    return raw.length;
  },

  /** Cache-aside helper: returns cached or runs loader, then stores result. */
  async remember(namespace, key, loader, ttl = TTL.MEDIUM) {
    const hit = await cache.get(namespace, key);
    if (hit !== undefined) return { value: hit, hit: true };
    const value = await loader();
    await cache.set(namespace, key, value, ttl);
    return { value, hit: false };
  },

  /** Wrap a loader in a write-through short cache for the given key(s). */
  async bust(namespace) {
    await cache.invalidateNamespace(namespace);
  },
};

export default cache;
