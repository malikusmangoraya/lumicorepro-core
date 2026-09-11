import { describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import cache from '../../services/cache/cache.service.js';

describe('Cache service (in-memory fallback)', () => {
  it('misses then remembers a value', async () => {
    const missing = await cache.get('ns', 'k1');
    expect(missing).toBeUndefined();

    const { value, hit } = await cache.remember('ns', 'k1', async () => ({ total: 42 }), cache.TTL.SHORT);
    expect(value).toEqual({ total: 42 });
    expect(hit).toBe(false);

    const second = await cache.remember('ns', 'k1', async () => ({ total: 0 }));
    expect(second.value).toEqual({ total: 42 }); // served from cache
    expect(second.hit).toBe(true);
  });

  it('stores TTL-expiring simple scalars', async () => {
    await cache.set('ns2', 'x', 'hello', 1);
    const val = await cache.get('ns2', 'x');
    expect(val).toBe('hello');
  });

  it('invalidates a namespace prefix', async () => {
    await cache.set('products', 'page1', [1]);
    await cache.set('products', 'page2', [2]);
    const cleared = await cache.invalidateNamespace('products');
    expect(cleared).toBeGreaterThanOrEqual(1);
    expect(await cache.get('products', 'page1')).toBeUndefined();
  });
});