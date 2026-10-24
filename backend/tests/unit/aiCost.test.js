import { describe, it, expect, beforeEach, jest } from '@jest/globals';

/**
 * aiCost services tests (spendEstimator + spendLedger).
 *
 * These two modules are the cost-accounting layer for AI spend: the estimator
 * feeds the admin dashboard and the ledger enforces the per-user daily budget
 * cap. Both ship without coverage despite deciding whether paid AI runs are
 * allowed to start.
 */

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };

let redisAvailable = false;
const fakeRedis = {
  get: jest.fn(),
  set: jest.fn(),
  incrbyfloat: jest.fn(),
  expire: jest.fn(),
  pipeline: jest.fn(),
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

const estimator = await import('../../services/aiCost/spendEstimator.service.js');
const ledger = await import('../../services/aiCost/spendLedger.service.js');

let uid = 0;
const uniqueUser = () => `test-user-${Date.now()}-${++uid}`;

beforeEach(() => {
  redisAvailable = false;
  jest.clearAllMocks();
});

describe('spendEstimator', () => {
  it('exposes the cost model config', () => {
    const cfg = estimator.getEstimatorConfig();
    expect(cfg.dailyGenLimit).toBeGreaterThan(0);
    expect(cfg.costPer1kTokens).toBeGreaterThan(0);
    expect(cfg.avgTokensPerGeneration).toBeGreaterThan(0);
  });

  it('estimates tokens per endpoint with a generation fallback', () => {
    expect(estimator.estimateTokensForRequest('chat')).toBe(2500);
    expect(estimator.estimateTokensForRequest('vision')).toBe(1200);
    expect(estimator.estimateTokensForRequest('unknown-endpoint')).toBe(18000);
  });

  it('returns an 8-day zeroed summary in-memory when Redis is down', async () => {
    const summary = await estimator.getSpendSummary();
    expect(summary.source).toBe('in-memory');
    expect(summary.daily).toHaveLength(8);
    expect(summary.daily[7].isToday).toBe(true);
    expect(summary.totals.requests).toBe(0);
    expect(summary.totals.estimatedCost).toBe(0);
  });

  it('aggregates Redis hash fields into per-endpoint and per-user totals', async () => {
    redisAvailable = true;
    const pipe = {
      hgetall: jest.fn(),
      exec: jest.fn().mockResolvedValue([
        [null, {
          'global:count': '3',
          'global:tokens': '9000',
          'endpoint:generation:count': '2',
          'endpoint:chat:count': '1',
          'user:u1:tokens': '7000',
          'user:u2:tokens': '2000',
        }],
        // remaining days empty
        ...Array.from({ length: 7 }, () => [null, {}]),
      ]),
    };
    fakeRedis.pipeline.mockReturnValueOnce(pipe);

    const summary = await estimator.getSpendSummary(8);
    expect(summary.source).toBe('redis');
    expect(summary.totals.requests).toBe(3);
    expect(summary.totals.estimatedTokens).toBe(9000);
    expect(summary.byEndpoint.generation).toBe(2);
    expect(summary.byEndpoint.chat).toBe(1);
    expect(summary.topUsers[0]).toEqual({ userId: 'u1', tokens: 7000 });
    // 9000 tokens at $0.02/1K = $0.18
    expect(summary.totals.estimatedCost).toBeCloseTo(0.18, 6);
  });

  it('weekly projection returns no warning with zero budget configured', () => {
    const proj = estimator.getWeeklyProjection();
    expect(proj.projectedTokens).toBeGreaterThanOrEqual(0);
    expect(proj.warning).toBeNull();
  });
});

describe('spendLedger', () => {
  it('estimateCostUsd converts tokens at the configured rate', () => {
    // default $0.02 per 1K tokens
    expect(ledger.estimateCostUsd(1000)).toBeCloseTo(0.02, 8);
    expect(ledger.estimateCostUsd(0)).toBe(0);
    expect(ledger.estimateCostUsd('junk')).toBe(0);
  });

  it('checkBudget always allows anonymous traffic (unscoped)', async () => {
    const res = await ledger.checkBudget(null, 999);
    expect(res.allowed).toBe(true);
    expect(res.scoped).toBe(false);
  });

  it('allows a run under the daily cap and records it', async () => {
    const userId = uniqueUser();
    const create = jest.fn().mockResolvedValue({});
    const res = await ledger.recordRun({ userId, tokens: 1000, ledgerModel: { create } });
    expect(res.persisted).toBe(true);
    expect(res.cost).toBeCloseTo(0.02, 8);
    expect(create).toHaveBeenCalledWith(
      expect.objectContaining({ user_id: userId, kind: 'run', estimated_tokens: 1000 })
    );

    const budget = await ledger.checkBudget(userId, 0.01);
    expect(budget.allowed).toBe(true);
    expect(budget.spentTodayUsd).toBeCloseTo(0.02, 6);
  });

  it('blocks a run that would cross the $5 daily cap', async () => {
    const userId = uniqueUser();
    const create = jest.fn().mockResolvedValue({});
    // Spend $4.90
    await ledger.recordRun({ userId, costUsd: 4.9, ledgerModel: { create } });

    const blocked = await ledger.checkBudget(userId, 0.2);
    expect(blocked.allowed).toBe(false);
    expect(blocked.budgetUsd).toBe(5);

    const allowed = await ledger.checkBudget(userId, 0.05);
    expect(allowed.allowed).toBe(true);
  });

  it('never breaks the caller when the ledger write fails', async () => {
    const userId = uniqueUser();
    const create = jest.fn().mockRejectedValue(new Error('db down'));
    const res = await ledger.recordRun({ userId, tokens: 500, ledgerModel: { create } });
    expect(res.persisted).toBe(false);
    expect(mockLogger.warn).toHaveBeenCalled();
  });

  it('alerts once when the daily budget is exceeded', async () => {
    const userId = uniqueUser();
    const create = jest.fn().mockResolvedValue({});
    await ledger.recordRun({ userId, costUsd: 6, ledgerModel: { create } });
    const warned = mockLogger.warn.mock.calls.some((c) => String(c[0]).includes('BUDGET EXCEEDED'));
    expect(warned).toBe(true);
  });

  it('uses Redis counters when available', async () => {
    redisAvailable = true;
    fakeRedis.incrbyfloat.mockResolvedValueOnce(1.5);
    fakeRedis.expire.mockResolvedValueOnce(1);
    const create = jest.fn().mockResolvedValue({});

    const userId = uniqueUser();
    await ledger.recordRun({ userId, costUsd: 1.5, ledgerModel: { create } });
    expect(fakeRedis.incrbyfloat).toHaveBeenCalled();
    expect(fakeRedis.expire).toHaveBeenCalled();
  });

  it('getLedgerSummary aggregates rows per endpoint', async () => {
    const findAll = jest.fn().mockResolvedValue([
      { endpoint: 'generation', estimated_tokens: 1000, estimated_cost_usd: 0.02 },
      { endpoint: 'generation', estimated_tokens: 2000, estimated_cost_usd: 0.04 },
      { endpoint: 'chat', estimated_tokens: 500, estimated_cost_usd: 0.01 },
    ]);
    const summary = await ledger.getLedgerSummary(7, { findAll });
    expect(summary.totalRuns).toBe(3);
    expect(summary.totalTokens).toBe(3500);
    expect(summary.totalCostUsd).toBeCloseTo(0.07, 6);
    expect(summary.byEndpoint.generation.runs).toBe(2);
    expect(summary.byEndpoint.chat.runs).toBe(1);
  });

  it('getLedgerSummary degrades gracefully on DB failure', async () => {
    const findAll = jest.fn().mockRejectedValue(new Error('no connection'));
    const summary = await ledger.getLedgerSummary(7, { findAll });
    expect(summary.error).toBe('no connection');
    expect(summary.totalRuns).toBe(0);
  });
});
