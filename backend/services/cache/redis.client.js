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

function getFallback() {
  if (!fallback) {
    fallback = {
      __memory: true,
      isMemory: true,
      async get(k) { return memoryStore.get(k) ?? null; },
      async set(k, v, mode, ttl) {
        memoryStore.set(k, v);
        if (mode === 'EX' && ttl) {
          setTimeout(() => memoryStore.delete(k), ttl * 1000);
        }
        return 'OK';
      },
      async del(...keys) { keys.forEach((k) => memoryStore.delete(k)); return keys.length; },
      async incrby(k, n) { const next = (Number(memoryStore.get(k)) || 0) + n; memoryStore.set(k, String(next)); return next; },
      async expire() { return 1; },
      async ttl() { return -1; },
      async exists(...keys) { return keys.some((k) => memoryStore.has(k)) ? 1 : 0; },
      async keys(p = '*') {
        const re = new RegExp('^' + p.replace(/\*/g, '.*') + '$');
        return [...memoryStore.keys()].filter((k) => re.test(k));
      },
      async sadd(key, member) {
        const list = memoryStore.get(key) ? memoryStore.get(key).split(',') : [];
        if (!list.includes(member)) list.push(member);
        memoryStore.set(key, list.join(','));
        return 1;
      },
      async smembers(key) {
        const raw = memoryStore.get(key);
        return raw ? raw.split(',').filter(Boolean) : [];
      },
      async srem(key, ...members) {
        const list = memoryStore.get(key) ? memoryStore.get(key).split(',') : [];
        const before = list.length;
        const next = list.filter((m) => !members.includes(m));
        memoryStore.set(key, next.join(','));
        return before - next.length;
      },
      async quit() { memoryStore.clear(); return 'OK'; },
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
