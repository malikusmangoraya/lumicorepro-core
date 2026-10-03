import { describe, it, expect, beforeEach, jest } from '@jest/globals';

/**
 * The in-memory Redis fallback. Its expiry used to be a bare
 * `setTimeout(ttl * 1000)`, which Node clamps to 1ms once the delay exceeds
 * 2^31-1 (~24.8 days). Any caller using a 30-day or 90-day TTL silently got
 * ~1ms retention — that is how refresh-token revocation became a no-op when
 * Redis was unavailable. These tests pin the corrected absolute-expiry
 * behaviour, including the overflow boundary.
 */

const MAX_TIMER_MS = 2 ** 31 - 1;

let redis;
let mod;

/**
 * Note the call shape: `getRedis()` is the raw client, so it takes the FULL
 * already-namespaced key plus (value, 'EX', ttl) - not (namespace, key, ...).
 * cache.service.js is what builds those namespaced keys.
 */
beforeEach(async () => {
  jest.resetModules();
  mod = await import('../../services/cache/redis.client.js');
  redis = mod.getRedis();
  await redis.quit();
});

describe('in-memory fallback - expiry', () => {
  it('stores and reads a value with a TTL', async () => {
    await redis.set('ns:k', 'v', 'EX', 60);
    expect(await redis.get('ns:k')).toBe('v');
  });

  it('returns null for a missing key', async () => {
    expect(await redis.get('ns:missing')).toBeNull();
  });

  it('keeps a 30-day TTL after the old 1ms clamp would have fired', async () => {
    await redis.set('ns:long', 'value', 'EX', 30 * 24 * 3600);
    // The old code scheduled this delete at 2_592_000_000ms, clamped to 1ms.
    await new Promise((r) => setTimeout(r, 60));
    expect(await redis.get('ns:long')).toBe('value');
  });

  it('keeps a 90-day TTL too', async () => {
    await redis.set('ns:longer', 'value', 'EX', 90 * 24 * 3600);
    await new Promise((r) => setTimeout(r, 30));
    expect(await redis.get('ns:longer')).toBe('value');
  });

  it('honours the exact overflow boundary', async () => {
    const maxSeconds = Math.floor(MAX_TIMER_MS / 1000);
    await redis.set('ns:edge', 'value', 'EX', maxSeconds);
    await new Promise((r) => setTimeout(r, 20));
    expect(await redis.get('ns:edge')).toBe('value');
  });

  it('still expires a short TTL', async () => {
    // 0.05s rounds to a real, sub-second wait.
    await redis.set('ns:short', 'value', 'EX', 0.05);
    expect(await redis.get('ns:short')).toBe('value');
    await new Promise((r) => setTimeout(r, 120));
    expect(await redis.get('ns:short')).toBeNull();
  });

  it('reports remaining TTL and -1 for no expiry', async () => {
    await redis.set('ns:a', 'v', 'EX', 60);
    const t = await redis.ttl('ns:a');
    expect(t).toBeGreaterThan(50);
    expect(t).toBeLessThanOrEqual(60);

    await redis.set('ns:b', 'v');
    expect(await redis.ttl('ns:b')).toBe(-1);
  });

  it('overwrites the previous TTL when the key is set again', async () => {
    await redis.set('ns:k', 'first', 'EX', 3600);
    await redis.set('ns:k', 'second', 'EX', 0.05);
    expect(await redis.get('ns:k')).toBe('second');
    await new Promise((r) => setTimeout(r, 120));
    expect(await redis.get('ns:k')).toBeNull();
  });

  it('exists() ignores expired keys', async () => {
    await redis.set('ns:gone', 'v', 'EX', 0.05);
    await new Promise((r) => setTimeout(r, 120));
    expect(await redis.exists('ns:gone')).toBe(0);
  });
});

describe('in-memory fallback - counters', () => {
  it('incrby accumulates and starts from 0', async () => {
    expect(await redis.incrby('c', 1)).toBe(1);
    expect(await redis.incrby('c', 4)).toBe(5);
    expect(await redis.get('c')).toBe('5');
  });

  it('incrby treats an expired counter as 0', async () => {
    await redis.set('c', '10', 'EX', 0.05);
    await new Promise((r) => setTimeout(r, 120));
    expect(await redis.incrby('c', 3)).toBe(3);
  });

  it('survives a counter that outlives the 32-bit timer limit', async () => {
    await redis.set('c', '1', 'EX', 30 * 24 * 3600);
    await new Promise((r) => setTimeout(r, 40));
    expect(await redis.incrby('c', 1)).toBe(2);
  });
});

describe('in-memory fallback - sets', () => {
  it('adds, lists and removes members without duplicates', async () => {
    await redis.sadd('s', 'a');
    await redis.sadd('s', 'a');
    await redis.sadd('s', 'b');
    expect(await redis.smembers('s')).toEqual(['a', 'b']);
    expect(await redis.srem('s', 'a')).toBe(1);
    expect(await redis.smembers('s')).toEqual(['b']);
  });

  it('sadd does not resurrect an expired set', async () => {
    await redis.set('s', 'a,b', 'EX', 0.05);
    await new Promise((r) => setTimeout(r, 120));
    await redis.sadd('s', 'c');
    expect(await redis.smembers('s')).toEqual(['c']);
  });
});

describe('in-memory fallback - keys and del', () => {
  it('lists only unexpired keys matching a glob', async () => {
    await redis.set('pre:a', 'a', 'EX', 60);
    await redis.set('pre:b', 'b', 'EX', 0.05);
    await redis.set('other:c', 'c', 'EX', 60);
    // Both pre:* keys are still live at t=0; only the glob is filtered here.
    expect((await redis.keys('pre:*')).sort()).toEqual(['pre:a', 'pre:b']);

    await new Promise((r) => setTimeout(r, 120));
    expect((await redis.keys('pre:*')).sort()).toEqual(['pre:a']);
  });

  it('del removes keys and reports how many existed', async () => {
    await redis.set('ns:x', 'v');
    await redis.set('ns:y', 'v');
    expect(await redis.del('ns:x', 'ns:y', 'ns:absent')).toBe(2);
    expect(await redis.get('ns:x')).toBeNull();
  });
});

describe('in-memory fallback - availability reporting', () => {
  it('reports itself as not real Redis', () => {
    expect(mod.isRedisAvailable()).toBe(false);
    expect(redis.isMemory).toBe(true);
  });
});
