import { describe, it, expect } from 'vitest';
import {
  toLocaleTag,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPercent,
} from '../../utils/localizedFormat';

describe('localizedFormat', () => {
  describe('toLocaleTag', () => {
    it('maps supported languages to BCP-47 tags', () => {
      expect(toLocaleTag('en')).toBe('en-US');
      expect(toLocaleTag('ur')).toBe('ur-PK');
      expect(toLocaleTag('ja')).toBe('ja-JP');
      expect(toLocaleTag('TR')).toBe('tr-TR');
    });
    it('falls back to en-US for unknown languages', () => {
      expect(toLocaleTag('xx')).toBe('en-US');
      expect(toLocaleTag('')).toBe('en-US');
    });
  });

  describe('formatDate', () => {
    it('formats a valid date', () => {
      const out = formatDate('2026-10-23T12:00:00Z', {}, 'en');
      expect(out).toMatch(/2026/);
      expect(out).toMatch(/Oct/);
    });
    it('returns empty string for invalid dates', () => {
      expect(formatDate('not-a-date')).toBe('');
    });
    it('respects explicit locale', () => {
      const de = formatDate('2026-10-23T12:00:00Z', {}, 'de');
      expect(de).toMatch(/Okt/);
    });
  });

  describe('formatDateTime', () => {
    it('includes hours and minutes', () => {
      const out = formatDateTime('2026-10-23T14:05:00Z', {}, 'en');
      expect(out).toMatch(/\d{1,2}:\d{2}/);
    });
  });

  describe('formatNumber', () => {
    it('uses locale grouping/decimals', () => {
      expect(formatNumber(1234567.89, {}, 'en')).toBe('1,234,567.89');
      expect(formatNumber(1234567.89, {}, 'de')).toBe('1.234.567,89');
    });
    it('formats zero and negatives', () => {
      expect(formatNumber(0, {}, 'en')).toBe('0');
      expect(formatNumber(-42, {}, 'en')).toBe('-42');
    });
  });

  describe('formatPercent', () => {
    it('renders a fraction as percent', () => {
      expect(formatPercent(0.125, { maximumFractionDigits: 1 }, 'en')).toBe('12.5%');
    });
  });
});
