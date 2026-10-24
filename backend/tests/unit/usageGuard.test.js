import { describe, it, expect, beforeEach, jest } from '@jest/globals';

/**
 * usageGuard middleware tests.
 *
 * The guard is the server-side cost protection for AI routes (daily limits,
 * circuit breaker, token caps). It had zero coverage while being the only
 * thing between the API and unbounded AI spend. Tests run against the
 * in-memory fallback (Redis unavailable) plus a faked Redis client for the
 * Redis branches. In-memory maps are module-level state, so every test uses
 * a unique IP/user id to stay isolated.
 */

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };

let redisAvailable = false;
const fakeRedis = {
  get: jest.fn(),
  incr: jest.fn(),
  expire: jest.fn(),
  set: jest.fn(),
  hincrby: jest.fn(),
};

jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({
  getRedis: () => fakeRedis,
  isRedisAvailable: () => redisAvailable,
}));

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

const guard = await import('../../middleware/usageGuard.js');

let ipCounter = 0;
const uniqueIp = () => `10.0.0.${++ipCounter}`;

function makeReq(overrides = {}) {
  return {
    ip: uniqueIp(),
    body: {},
    ...overrides,
  };
}

function makeRes() {
  const headers = {};
  const res = {
    statusCode: null,
    body: null,
    headers,
    setHeader(k, v) {
      headers[k] = v;
    },
    status(code) {
      res.statusCode = code;
      return res;
    },
    json(payload) {
      res.body = payload;
      return res;
    },
  };
  return res;
}

beforeEach(() => {
  redisAvailable = false;
  jest.clearAllMocks();
});

describe('tokenCap', () => {
  it('clamps a user-supplied max_tokens above the cap', () => {
    const mw = guard.tokenCap('generation');
    const req = makeReq({ body: { max_tokens: 999999 } });
    mw(req, makeRes(), () => {});
    expect(req.body.max_tokens).toBe(guard.MAX_TOKENS_GENERATION);
    expect(req.body._max_tokens_cap).toBe(guard.MAX_TOKENS_GENERATION);
  });

  it('keeps a max_tokens value below the cap', () => {
    const mw = guard.tokenCap('chat');
    const req = makeReq({ body: { max_tokens: 100 } });
    mw(req, makeRes(), () => {});
    expect(req.body.max_tokens).toBe(100);
    expect(req.body._max_tokens_cap).toBe(guard.MAX_TOKENS_CHAT);
  });

  it('injects the cap even when no max_tokens is supplied', () => {
    const mw = guard.tokenCap('vision');
    const req = makeReq({ body: {} });
    const next = jest.fn();
    mw(req, makeRes(), next);
    expect(req.body._max_tokens_cap).toBe(guard.MAX_TOKENS_VISION);
    expect(next).toHaveBeenCalled();
  });

  it('falls back to the generation cap for unknown endpoint types', () => {
    const mw = guard.tokenCap('nonsense');
    const req = makeReq({ body: {} });
    mw(req, makeRes(), () => {});
    expect(req.body._max_tokens_cap).toBe(guard.MAX_TOKENS_GENERATION);
  });
});

describe('dailyGenLimit (in-memory fallback)', () => {
  it('allows requests up to the limit, then returns 429', async () => {
    const ip = uniqueIp();
    const mw = guard.dailyGenLimit(2);

    const res1 = makeRes();
    const next1 = jest.fn();
    await mw(makeReq({ ip }), res1, next1);
    expect(next1).toHaveBeenCalled();
    expect(res1.headers['X-Daily-Limit']).toBe('2');
    expect(res1.headers['X-Daily-Used']).toBe('1');

    const res2 = makeRes();
    const next2 = jest.fn();
    await mw(makeReq({ ip }), res2, next2);
    expect(next2).toHaveBeenCalled();

    const res3 = makeRes();
    const next3 = jest.fn();
    await mw(makeReq({ ip }), res3, next3);
    expect(next3).not.toHaveBeenCalled();
    expect(res3.statusCode).toBe(429);
    expect(res3.body.success).toBe(false);
    expect(res3.body.error.code).toBe('DAILY_LIMIT_EXCEEDED');
    expect(res3.headers['X-Daily-Remaining']).toBe('0');
  });

  it('tracks different clients independently', async () => {
    const mw = guard.dailyGenLimit(1);
    const ipA = uniqueIp();
    const ipB = uniqueIp();

    // Client A uses its one request
    const nextA = jest.fn();
    await mw(makeReq({ ip: ipA }), makeRes(), nextA);
    expect(nextA).toHaveBeenCalled();

    // A brand-new client must still pass
    const nextB = jest.fn();
    await mw(makeReq({ ip: ipB }), makeRes(), nextB);
    expect(nextB).toHaveBeenCalled();

    // And client A is now over the limit
    const resA2 = makeRes();
    const nextA2 = jest.fn();
    await mw(makeReq({ ip: ipA }), resA2, nextA2);
    expect(nextA2).not.toHaveBeenCalled();
    expect(resA2.statusCode).toBe(429);
  });

  it('prefers authenticated user id over IP for the counter key', async () => {
    const mw = guard.dailyGenLimit(1);
    const userId = `user-${Date.now()}`;

    await mw(makeReq({ user: { id: userId } }), makeRes(), jest.fn());
    const res = makeRes();
    const next = jest.fn();
    // Same user from a different IP must still be blocked
    await mw(makeReq({ user: { id: userId } }), res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
  });
});

describe('dailyChatLimit (in-memory fallback)', () => {
  it('returns 429 with CHAT code after the limit', async () => {
    const ip = uniqueIp();
    const mw = guard.dailyChatLimit(1);
    await mw(makeReq({ ip }), makeRes(), jest.fn());

    const res = makeRes();
    const next = jest.fn();
    await mw(makeReq({ ip }), res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
    expect(res.body.error.code).toBe('DAILY_CHAT_LIMIT_EXCEEDED');
  });
});

describe('circuitBreaker (in-memory fallback)', () => {
  it('blocks after the window threshold and sets Retry-After', async () => {
    const ip = uniqueIp();
    const mw = guard.circuitBreaker();
    const CB_MAX = 10; // default when AI_CB_MAX_REQUESTS is unset

    for (let i = 0; i < CB_MAX; i++) {
      const next = jest.fn();
      await mw(makeReq({ ip }), makeRes(), next);
      expect(next).toHaveBeenCalled();
    }

    const res = makeRes();
    const next = jest.fn();
    await mw(makeReq({ ip }), res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
    expect(res.body.error.code).toBe('CIRCUIT_BREAKER');
    expect(res.headers['Retry-After']).toBeDefined();
    expect(res.headers['X-Circuit-Breaker']).toBe('active');
  });

  it('lets normal-rate traffic through', async () => {
    const mw = guard.circuitBreaker();
    const res = makeRes();
    const next = jest.fn();
    await mw(makeReq(), res, next);
    expect(next).toHaveBeenCalled();
    expect(res.statusCode).toBeNull();
  });
});

describe('redis-backed branches', () => {
  it('daily limit uses Redis counters when available', async () => {
    redisAvailable = true;
    fakeRedis.incr.mockResolvedValueOnce(1);
    fakeRedis.expire.mockResolvedValueOnce(1);

    const mw = guard.dailyGenLimit(3);
    const res = makeRes();
    const next = jest.fn();
    await mw(makeReq(), res, next);
    expect(next).toHaveBeenCalled();
    expect(fakeRedis.incr).toHaveBeenCalled();
    expect(fakeRedis.expire).toHaveBeenCalled(); // TTL set on first increment
  });

  it('daily limit blocks when the Redis counter exceeds the limit', async () => {
    redisAvailable = true;
    fakeRedis.incr.mockResolvedValueOnce(99);

    const mw = guard.dailyGenLimit(3);
    const res = makeRes();
    const next = jest.fn();
    await mw(makeReq(), res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
  });

  it('circuit breaker honours a Redis-stored block', async () => {
    redisAvailable = true;
    // Block timestamp one hour in the future
    fakeRedis.get.mockResolvedValueOnce(String(Math.ceil(Date.now() / 1000) + 3600));

    const mw = guard.circuitBreaker();
    const res = makeRes();
    const next = jest.fn();
    await mw(makeReq(), res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
    expect(Number(res.headers['Retry-After'])).toBeGreaterThan(0);
  });

  it('falls back to memory when Redis throws', async () => {
    redisAvailable = true;
    fakeRedis.incr.mockRejectedValueOnce(new Error('ECONNREFUSED'));

    const mw = guard.dailyGenLimit(1);
    const res = makeRes();
    const next = jest.fn();
    await mw(makeReq(), res, next);
    expect(next).toHaveBeenCalled();
  });
});

describe('recordUsage', () => {
  it('records in memory without throwing when Redis is unavailable', async () => {
    await expect(
      guard.recordUsage({ userId: 'u1', ip: uniqueIp(), endpoint: 'generate', estimatedTokens: 42 })
    ).resolves.toBeUndefined();
  });

  it('writes hash counters when Redis is available', async () => {
    redisAvailable = true;
    fakeRedis.hincrby.mockResolvedValue(1);
    fakeRedis.expire.mockResolvedValue(1);
    await guard.recordUsage({ userId: 'u1', ip: uniqueIp(), endpoint: 'generate', estimatedTokens: 42 });
    expect(fakeRedis.hincrby).toHaveBeenCalled();
    expect(fakeRedis.expire).toHaveBeenCalled();
  });
});

describe('aiCostGuard stack', () => {
  it('returns circuit breaker + daily limit + token cap', () => {
    const stack = guard.aiCostGuard('generation');
    expect(Array.isArray(stack)).toBe(true);
    expect(stack).toHaveLength(3);
    stack.forEach((mw) => expect(typeof mw).toBe('function'));
  });
});
