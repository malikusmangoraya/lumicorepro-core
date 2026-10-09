import { describe, it, expect, jest, beforeEach } from '@jest/globals';

const findAll = jest.fn();

jest.unstable_mockModule('../../models/FeatureFlag.js', () => ({
  __esModule: true,
  default: { findAll },
}));

const { isEnabled, rolloutBucket, clearFlagCache } = await import(
  '../../services/featureFlag.service.js'
);

describe('Feature flags', () => {
  beforeEach(() => {
    findAll.mockReset();
    clearFlagCache();
  });

  it('is fail-closed for unknown flags', async () => {
    findAll.mockResolvedValue([]);
    await expect(isEnabled('nope', 1)).resolves.toBe(false);
  });

  it('is fail-closed when the database is down', async () => {
    findAll.mockRejectedValue(new Error('db down'));
    await expect(isEnabled('anything', 1)).resolves.toBe(false);
  });

  it('returns true for fully rolled out flags', async () => {
    findAll.mockResolvedValue([{ key: 'x', enabled: true, rollout: 100 }]);
    await expect(isEnabled('x', 7)).resolves.toBe(true);
  });

  it('returns false for disabled flags', async () => {
    findAll.mockResolvedValue([{ key: 'x', enabled: false, rollout: 100 }]);
    await expect(isEnabled('x', 7)).resolves.toBe(false);
  });

  it('assigns users deterministically to a partial rollout', async () => {
    findAll.mockResolvedValue([{ key: 'x', enabled: true, rollout: 50 }]);
    const first = await isEnabled('x', 42);
    clearFlagCache();
    const second = await isEnabled('x', 42);
    expect(first).toBe(second);
    // Bucket is uniform-ish: across 200 users both sides must be represented.
    clearFlagCache();
    const outcomes = new Set();
    for (let id = 1; id <= 200; id += 1) {
      clearFlagCache();
      outcomes.add(await isEnabled('x', id));
    }
    expect(outcomes).toEqual(new Set([true, false]));
  });

  it('rolloutBucket is stable and bounded', () => {
    expect(rolloutBucket('x', 1)).toBe(rolloutBucket('x', 1));
    for (let id = 1; id <= 500; id += 1) {
      const b = rolloutBucket('x', id);
      expect(b).toBeGreaterThanOrEqual(0);
      expect(b).toBeLessThan(100);
    }
  });
});
