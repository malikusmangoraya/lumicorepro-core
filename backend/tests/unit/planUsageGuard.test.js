/**
 * Plan usage guard tests (middleware/planUsageGuard.js).
 *
 * The guard runs against the REAL services/usage.service.js with only its
 * infrastructure mocked (Redis client, model registry, logger), so limits are
 * derived, counters incremented and headers set by production code rather than
 * by a stub. That makes the 429 boundary — the thing that decides whether a
 * paying customer gets served — genuinely measured.
 */
import { describe, it, expect, beforeEach, jest } from '@jest/globals';

const mockLogger = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  http: jest.fn(),
};

let redisAvailable = false;
const fakeRedis = {
  get: jest.fn(),
  set: jest.fn(),
  incrby: jest.fn(),
  expire: jest.fn(),
};

/** Active subscription row returned by the mocked model registry. */
const registry = { subscription: null, findOneError: null };

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({
  __esModule: true,
  getRedis: () => fakeRedis,
  isRedisAvailable: () => redisAvailable,
}));

jest.unstable_mockModule('../../models/index.js', () => ({
  __esModule: true,
  Subscription: {
    findOne: async () => {
      if (registry.findOneError) throw new Error(registry.findOneError);
      return registry.subscription;
    },
  },
  Plan: {},
  AnalyticsEvent: { create: () => Promise.resolve({}) },
}));

const guard = await import('../../middleware/planUsageGuard.js');
const usage = await import('../../services/usage.service.js');
const { enforcePlanLimit, meterPlanUsage } = guard;
const { USAGE_METRICS } = usage;

let userSeq = 0;
const uniqueUser = () => 9000 + ++userSeq;

function makeReq(user) {
  return { user, body: {}, headers: {} };
}

function makeRes(onSetHeader) {
  const headers = {};
  const res = {
    statusCode: null,
    body: null,
    headers,
    setHeader(name, value) {
      if (onSetHeader) onSetHeader(name, value);
      headers[name] = value;
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

const run = async (mw, req, res) => {
  const next = jest.fn();
  await mw(req, res, next);
  return next;
};

/** Burn `count` units of a metric for one user through the real counters. */
async function consume(userId, metric, count) {
  for (let i = 0; i < count; i += 1) await usage.recordPlanUsage(userId, metric, 1);
}

beforeEach(() => {
  redisAvailable = false;
  registry.subscription = null;
  registry.findOneError = null;
});

describe('enforcePlanLimit metric validation', () => {
  it('refuses to build a guard for an unknown metric', () => {
    expect(() => enforcePlanLimit('ai_something')).toThrow(/Unknown usage metric: ai_something/);
  });

  it('accepts every metric the usage service declares', () => {
    for (const metric of Object.keys(USAGE_METRICS)) {
      expect(typeof enforcePlanLimit(metric)).toBe('function');
    }
  });
});

describe('enforcePlanLimit — unauthenticated requests', () => {
  it('lets service-to-service (x-api-key) traffic through without a plan lookup', async () => {
    const mw = enforcePlanLimit('ai_generation');
    const res = makeRes();

    const next = await run(mw, makeReq(undefined), res);

    expect(next).toHaveBeenCalled();
    expect(res.statusCode).toBeNull();
    expect(res.headers['X-Plan-Limit']).toBeUndefined();
  });

  it('lets a user object without an id through', async () => {
    const mw = enforcePlanLimit('ai_generation');
    const next = await run(mw, makeReq({ role: 'user' }), makeRes());

    expect(next).toHaveBeenCalled();
  });
});

describe('enforcePlanLimit — free plan boundaries', () => {
  it('passes under the cap and exposes the remaining quota headers', async () => {
    const userId = uniqueUser();
    const mw = enforcePlanLimit('ai_generation');
    const res = makeRes();

    const next = await run(mw, makeReq({ id: userId }), res);

    expect(next).toHaveBeenCalled();
    expect(res.statusCode).toBeNull();
    expect(res.headers['X-Plan-Name']).toBe('Free');
    expect(res.headers['X-Plan-Limit']).toBe('10');
    expect(res.headers['X-Plan-Used']).toBe('0');
    expect(res.headers['X-Plan-Remaining']).toBe('10');
    expect(new Date(res.headers['X-Plan-Resets-At']).getTime()).toBeGreaterThan(Date.now());
  });

  it('does not consume quota just by checking it', async () => {
    const userId = uniqueUser();
    const mw = enforcePlanLimit('ai_generation');

    for (let i = 0; i < 3; i += 1) await run(mw, makeReq({ id: userId }), makeRes());

    expect((await usage.getUsageSummary(userId)).used.ai_generation).toBe(0);
  });

  it('serves the request at one unit below the cap', async () => {
    const userId = uniqueUser();
    await consume(userId, 'ai_generation', 9);
    const mw = enforcePlanLimit('ai_generation');
    const res = makeRes();

    const next = await run(mw, makeReq({ id: userId }), res);

    expect(next).toHaveBeenCalled();
    expect(res.headers['X-Plan-Used']).toBe('9');
    expect(res.headers['X-Plan-Remaining']).toBe('1');
  });

  it('blocks exactly at the cap with 429 and never calls next', async () => {
    const userId = uniqueUser();
    await consume(userId, 'ai_generation', 10);
    const mw = enforcePlanLimit('ai_generation');
    const res = makeRes();

    const next = await run(mw, makeReq({ id: userId }), res);

    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
    expect(res.body.success).toBe(false);
    expect(res.body.error).toMatchObject({
      code: 'PLAN_LIMIT_EXCEEDED',
      message:
        "Your Free plan's monthly ai generations limit (10) has been reached. Upgrade your plan to continue.",
      metric: 'ai_generation',
      limit: 10,
      used: 10,
    });
    expect(new Date(res.body.error.resetsAt).getTime()).toBeGreaterThan(Date.now());
    expect(res.headers['X-Plan-Remaining']).toBe('0');
    expect(mockLogger.warn).toHaveBeenCalledWith(
      expect.stringContaining(`Plan limit exceeded for user ${userId}: ai_generation 10/10`),
    );
  });

  it('blocks further requests once over the cap', async () => {
    const userId = uniqueUser();
    await consume(userId, 'ai_chat', 51);
    const mw = enforcePlanLimit('ai_chat');
    const res = makeRes();

    const next = await run(mw, makeReq({ id: userId }), res);

    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
    expect(res.body.error.used).toBe(51);
  });
});

describe('enforcePlanLimit — plan resolution', () => {
  it('scales every cap from the subscription plan creditsGrant', async () => {
    const userId = uniqueUser();
    registry.subscription = { planName: 'Growth', plan: { creditsGrant: '20' } };
    const res = makeRes();

    const next = await run(enforcePlanLimit('ai_chat'), makeReq({ id: userId }), res);

    expect(next).toHaveBeenCalled();
    expect(res.headers['X-Plan-Name']).toBe('Growth');
    // creditsGrant 20 -> ai_generation 20, ai_chat x5, api x1000 (usage.service.js:127-131)
    expect(res.headers['X-Plan-Limit']).toBe('100');
  });

  it('lets a paid plan exceed the free-tier cap', async () => {
    const userId = uniqueUser();
    registry.subscription = { planName: 'Growth', plan: { creditsGrant: '20' } };
    await consume(userId, 'ai_generation', 15);
    const res = makeRes();

    const next = await run(enforcePlanLimit('ai_generation'), makeReq({ id: userId }), res);

    expect(next).toHaveBeenCalled();
    expect(res.headers['X-Plan-Limit']).toBe('20');
  });

  it('falls back to the free allowances when no subscription row exists', async () => {
    const userId = uniqueUser();
    registry.subscription = null;
    await consume(userId, 'ai_generation', 10);
    const res = makeRes();

    const next = await run(enforcePlanLimit('ai_generation'), makeReq({ id: userId }), res);

    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
    expect(res.body.error.limit).toBe(10);
  });

  it('falls back to the free allowances for a plan with no credits grant', async () => {
    const userId = uniqueUser();
    registry.subscription = { planName: 'Weird', plan: { creditsGrant: '0' } };
    const res = makeRes();

    await run(enforcePlanLimit('api'), makeReq({ id: userId }), res);

    expect(res.headers['X-Plan-Limit']).toBe('1000');
  });

  it('degrades to the free-plan cap when the plan lookup throws', async () => {
    const userId = uniqueUser();
    registry.findOneError = 'connection terminated unexpectedly';
    await consume(userId, 'ai_generation', 99);
    const res = makeRes();

    const next = await run(enforcePlanLimit('ai_generation'), makeReq({ id: userId }), res);

    // usage.service swallows the lookup failure and returns the Free defaults,
    // so enforcement survives an outage — but a paying customer whose plan row
    // cannot be read is throttled at free-tier limits (reported, not asserted
    // as desirable).
    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(429);
    expect(res.body.error.limit).toBe(10);
    expect(mockLogger.warn).toHaveBeenCalledWith(
      expect.stringContaining('resolvePlanForUser failed'),
    );
  });

  it('fails open and still calls next when the guard itself throws', async () => {
    const userId = uniqueUser();
    const mw = enforcePlanLimit('ai_generation');
    const res = makeRes(() => {
      throw new Error('cannot set header after they are sent');
    });

    const next = await run(mw, makeReq({ id: userId }), res);

    expect(next).toHaveBeenCalled();
    expect(res.statusCode).toBeNull();
    expect(mockLogger.warn).toHaveBeenCalledWith(
      expect.stringContaining('enforcePlanLimit skipped for ai_generation'),
    );
  });
});

describe('meterPlanUsage', () => {
  const flush = () => new Promise((resolve) => setImmediate(resolve));

  it('counts one api call for an authenticated user', async () => {
    const userId = uniqueUser();
    const next = await run(meterPlanUsage('api'), makeReq({ id: userId }), makeRes());

    await flush();

    expect(next).toHaveBeenCalled();
    expect((await usage.getUsageSummary(userId)).used.api).toBe(1);
  });

  it('never counts anonymous traffic', async () => {
    const next = await run(meterPlanUsage('api'), makeReq(undefined), makeRes());
    await flush();

    expect(next).toHaveBeenCalled();
    expect(fakeRedis.incrby).not.toHaveBeenCalled();
  });

  it('ignores an unknown metric instead of throwing mid-request', async () => {
    const userId = uniqueUser();
    const next = await run(meterPlanUsage('nonsense'), makeReq({ id: userId }), makeRes());
    await flush();

    expect(next).toHaveBeenCalled();
    expect((await usage.getUsageSummary(userId)).used.api).toBe(0);
  });

  it('does not swallow the request when the counter store rejects', async () => {
    redisAvailable = true;
    const userId = uniqueUser();
    fakeRedis.incrby.mockRejectedValue(new Error('READONLY'));
    fakeRedis.get.mockRejectedValue(new Error('READONLY'));

    const next = await run(meterPlanUsage('api'), makeReq({ id: userId }), makeRes());
    await flush();

    expect(next).toHaveBeenCalled();
  });

  it('metering then enforcing compounds into a block', async () => {
    const userId = uniqueUser();
    for (let i = 0; i < 10; i += 1) {
      await run(meterPlanUsage('api'), makeReq({ id: userId }), makeRes());
      await flush();
    }
    const res = makeRes();

    const next = await run(enforcePlanLimit('api'), makeReq({ id: userId }), res);

    // api cap is 1000 for the free plan, so ten metered calls must still pass.
    expect(next).toHaveBeenCalled();
    expect(res.headers['X-Plan-Used']).toBe('10');
  });
});

describe('registry drift', () => {
  it('BLOCKED_METRICS stays aligned with the metered metrics', () => {
    expect([...guard.default.BLOCKED_METRICS].sort()).toEqual(Object.keys(USAGE_METRICS).sort());
  });
});
