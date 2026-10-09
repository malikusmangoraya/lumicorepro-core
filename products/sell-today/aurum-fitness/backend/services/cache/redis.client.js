/**
 * Redis Connection Singleton
 * --------------------------
 * Lazily connects to Redis (ioredis). Gracefully degrades to a no-op in-memory
 * fallback when Redis is unreachable, so the app still works offline/during dev.
 * Exposes the raw client plus helpers to detect availability.
 */
import Redis from 'ioredis';

let client = null;
let fallback = null;
let connecting = false;

const memoryStore = new Map();

export function getRedis() {
  if (client) return client;
  if (fallback) return fallback;
  return getFallback();
}

// Node stores timer delays in a 32-bit signed int, so any setTimeout() over
// ~24.8 days is silently clamped to 1ms. Refresh-token revocation uses a 30-day
// TTL (2592000s -> 2592000000ms), which meant that whenever Redis was
// unavailable and this in-memory fallback was used, a revoked refresh token
// became valid again after 1ms. Store an absolute expiry instead and check it on
// read: no 32-bit limit, and it survives timer loss across event-loop stalls.
const MAX_TIMER_MS = 2 ** 31 - 1;

// value -> { value, expiresAt } | plain value for non-expiring entries
const readEntry = (k) => {
  const entry = memoryStore.get(k);
  if (entry === undefined) return undefined;
  const { value, expiresAt } =
    entry && entry.__expired !== undefined ? entry : { value: entry, expiresAt: 0 };
  if (expiresAt && Date.now() >= expiresAt) {
    memoryStore.delete(k);
    return undefined;
  }
  return value;
};

const writeEntry = (k, value, ttlSeconds) => {
  const expiresAt = ttlSeconds ? Date.now() + ttlSeconds * 1000 : 0;
  memoryStore.set(k, { __expired: true, value, expiresAt });
  // Reap eagerly only while the delay fits a 32-bit timer; otherwise lazy
  // expiry on read is the single source of truth.
  if (expiresAt) {
    const delay = expiresAt - Date.now();
    if (delay <= MAX_TIMER_MS) {
      setTimeout(() => {
        if (readEntry(k) === undefined) memoryStore.delete(k);
      }, delay);
    }
  }
  return 'OK';
};

function getFallback() {
  if (!fallback) {
    fallback = {
      __memory: true,
      isMemory: true,
      async get(k) {
        const v = readEntry(k);
        return v === undefined ? null : v;
      },
      async set(k, v, mode, ttl) {
        return writeEntry(k, v, mode === 'EX' ? Number(ttl) : 0);
      },
      async del(...keys) {
        let n = 0;
        for (const k of keys) if (memoryStore.delete(k)) n += 1;
        return n;
      },
      async incrby(k, n) {
        const next = (Number(readEntry(k)) || 0) + n;
        writeEntry(k, String(next), 0);
        return next;
      },
      async expire(k, ttl) {
        writeEntry(k, readEntry(k) ?? '', Number(ttl));
        return 1;
      },
      async ttl(k) {
        const entry = memoryStore.get(k);
        if (!entry || !entry.__expired) return -1;
        if (!entry.expiresAt) return -1;
        return Math.max(0, Math.ceil((entry.expiresAt - Date.now()) / 1000));
      },
      async exists(...keys) {
        return keys.some((k) => readEntry(k) !== undefined) ? 1 : 0;
      },
      async keys(p = '*') {
        const re = new RegExp('^' + p.replace(/\*/g, '.*') + '$');
        return [...memoryStore.keys()].filter((k) => re.test(k) && readEntry(k) !== undefined);
      },
      async sadd(key, member) {
        const list = (readEntry(key) || '').split(',').filter(Boolean);
        if (!list.includes(member)) list.push(member);
        writeEntry(key, list.join(','), 0);
        return 1;
      },
      async smembers(key) {
        const raw = readEntry(key);
        return raw ? raw.split(',').filter(Boolean) : [];
      },
      async srem(key, ...members) {
        const list = (readEntry(key) || '').split(',').filter(Boolean);
        const before = list.length;
        const next = list.filter((m) => !members.includes(m));
        writeEntry(key, next.join(','), 0);
        return before - next.length;
      },
      async quit() {
        memoryStore.clear();
        return 'OK';
      },
    };
  }
  return fallback;
}

export function isRedisAvailable() {
  return !!client && !client.isMemory;
}

/**
 * Connect to Redis. Resolves true if connected, false if unreachable
 * (the in-memory fallback is used instead). Safe to call multiple times.
 */
export async function connectRedis(url = process.env.REDIS_URL || 'redis://localhost:6379') {
  if (client || fallback) return isRedisAvailable();
  if (connecting) return isRedisAvailable();
  connecting = true;
  try {
    if (process.env.REDIS_DISABLED === 'true') {
      client = null;
      return false;
    }
    const c = new Redis(url, {
      maxRetriesPerRequest: 2,
      lazyConnect: true,
      enableOfflineQueue: false,
      retryStrategy: () => null,
      connectTimeout: 2000,
    });
    await c.connect();
    c.on('error', () => {});
    client = c;
    return true;
  } catch (err) {
    client = null;
    return false;
  } finally {
    connecting = false;
  }
}

export async function disconnectRedis() {
  try {
    if (client) await client.quit();
  } catch {
    /* ignore */
  }
  client = null;
}

export default getRedis;
