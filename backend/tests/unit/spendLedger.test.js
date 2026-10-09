import { describe, it, expect, beforeEach, jest } from '@jest/globals';

// Redis is unavailable in unit tests → the in-memory fallback path runs.
process.env.AI_DAILY_BUDGET_USD = '1';

describe('AI spend ledger + hard budgets', () => {
  let spendLedger;
  let ledgerRows;

  beforeEach(async () => {
    jest.resetModules();
    ledgerRows = [];
    spendLedger = await import('../../services/aiCost/spendLedger.service.js');
  });

  function fakeLedgerModel() {
    return { create: jest.fn(async (row) => { ledgerRows.push(row); return row; }) };
  }

  it('estimates cost from tokens', () => {
    // 1000 tokens at the default $0.02/1K → $0.02
    expect(spendLedger.estimateCostUsd(1000)).toBeCloseTo(0.02, 6);
  });

  it('allows a run inside the budget and accumulates spend', async () => {
    const first = await spendLedger.checkBudget('u1', 0.4);
    expect(first.allowed).toBe(true);
    await spendLedger.recordRun({ userId: 'u1', tokens: 20000, ledgerModel: fakeLedgerModel() });
    const second = await spendLedger.checkBudget('u1', 0.5);
    expect(second.allowed).toBe(true);
    expect(second.spentTodayUsd).toBeCloseTo(0.4, 3);
    const third = await spendLedger.checkBudget('u1', 0.7);
    expect(third.allowed).toBe(false); // 0.4 already spent + 0.7 projected > 1.0 cap
  });

  it('records exactly one ledger row per run', async () => {
    const model = fakeLedgerModel();
    await spendLedger.recordRun({ userId: 'u2', runId: 'run-9', tokens: 1000, ledgerModel: model });
    expect(model.create).toHaveBeenCalledTimes(1);
    expect(ledgerRows[0].run_id).toBe('run-9');
    expect(ledgerRows[0].estimated_cost_usd).toBeCloseTo(0.02, 6);
  });

  it('survives a broken ledger backend without throwing', async () => {
    const model = { create: jest.fn(async () => { throw new Error('db down'); }) };
    const result = await spendLedger.recordRun({ userId: 'u3', tokens: 1000, ledgerModel: model });
    expect(result.persisted).toBe(false);
    expect(result.cost).toBeGreaterThan(0);
  });

  it('unknown users never trip budget state', async () => {
    const verdict = await spendLedger.checkBudget(null, 999);
    expect(verdict.allowed).toBe(true);
  });
});
