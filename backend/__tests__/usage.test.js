import { describe, it, expect } from '@jest/globals';
import {
  currentMonthKey,
  nextMonthReset,
  resolvePlanLimits,
  USAGE_METRICS,
} from '../services/usage.service.js';

describe('Plan Usage Service', () => {
  describe('currentMonthKey / nextMonthReset', () => {
    it('should format the billing month as YYYY-M', () => {
      expect(currentMonthKey(new Date(Date.UTC(2026, 8, 1)))).toBe('2026-9');
      expect(currentMonthKey(new Date(Date.UTC(2026, 0, 1)))).toBe('2026-1');
    });

    it('should return the next month boundary in ms', () => {
      const reset = nextMonthReset(new Date(Date.UTC(2026, 0, 15)));
      expect(reset).toBe(Date.UTC(2026, 1, 1));
      const futureReset = nextMonthReset(new Date(Date.now() + 86400000));
      expect(futureReset).toBeGreaterThan(Date.now());
    });
  });

  describe('resolvePlanLimits', () => {
    it('should return free-tier defaults when no plan is active', () => {
      const limits = resolvePlanLimits(null);
      expect(limits).toEqual({ ai_generation: 10, ai_chat: 50, api: 1000 });
    });

    it('should scale limits from the plan creditsGrant', () => {
      const limits = resolvePlanLimits({ creditsGrant: 500 });
      expect(limits.ai_generation).toBe(500);
      expect(limits.ai_chat).toBe(500 * USAGE_METRICS.ai_chat.multiplier);
      expect(limits.api).toBe(500 * USAGE_METRICS.api.multiplier);
    });

    it('should floor at 1 and fall back for invalid credits', () => {
      expect(resolvePlanLimits({ creditsGrant: 0 }).ai_generation).toBe(10);
      expect(resolvePlanLimits({ creditsGrant: 'nope' }).ai_generation).toBe(10);
      expect(resolvePlanLimits({ creditsGrant: 0.2 }).ai_generation).toBe(1);
    });
  });
});