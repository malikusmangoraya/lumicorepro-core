import { describe, expect, it } from 'vitest';
import {
  formatCurrency,
  formatMileage,
  orderNumber,
  parseJson,
  slugify,
} from '@/lib/utils';

describe('formatCurrency', () => {
  it('uses the listing currency and never converts', () => {
    expect(formatCurrency(219500, 'USD')).toContain('219,500');
    expect(formatCurrency(219500, 'EUR', 'de-DE')).toContain('219.500');
  });

  it('drops cents for whole amounts', () => {
    expect(formatCurrency(118000, 'USD')).not.toContain('.00');
  });
});

describe('formatMileage', () => {
  it('keeps the unit the listing declares', () => {
    expect(formatMileage(4200, 'mi')).toBe('4,200 mi');
    expect(formatMileage(6800, 'km')).toBe('6,800 km');
  });
});

describe('slugify', () => {
  it('builds a URL-safe slug', () => {
    expect(slugify('2022 Porsche 911 GT3')).toBe('2022-porsche-911-gt3');
    expect(slugify('Aston Martin  Vantage!')).toBe('aston-martin-vantage');
  });

  it('strips accents rather than dropping the word', () => {
    expect(slugify('Huracán Performante')).toBe('huracn-performante');
  });
});

describe('parseJson', () => {
  it('returns the parsed value', () => {
    expect(parseJson('[{"url":"/a.svg","alt":"a"}]', [])).toEqual([{ url: '/a.svg', alt: 'a' }]);
  });

  it('falls back instead of throwing on corrupt data', () => {
    expect(parseJson('{not json', [])).toEqual([]);
    expect(parseJson(null, [])).toEqual([]);
  });
});

describe('orderNumber', () => {
  it('is stable and zero-padded', () => {
    expect(orderNumber(7)).toMatch(/^APX-\d{4}-00007$/);
  });
});
