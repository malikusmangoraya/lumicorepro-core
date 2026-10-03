import { describe, it, expect } from '@jest/globals';
import {
  calculateTax,
  getTaxInfo,
  getAllTaxRates,
  getUSStateTaxRates,
  formatTaxDisplay,
} from '../../utils/taxCalculator.js';

describe('taxCalculator - calculateTax', () => {
  it('returns a zeroed result for a non-positive amount', () => {
    const result = calculateTax({ amount: 0, country: 'DE' });
    expect(result).toMatchObject({ amount: 0, rate: 0, type: 'NONE', total: 0 });
  });

  it('returns a zeroed result for a negative amount', () => {
    expect(calculateTax({ amount: -50, country: 'DE' })).toMatchObject({
      amount: 0,
      total: 0,
      type: 'NONE',
    });
  });

  it('applies EU VAT as an exclusive amount', () => {
    const result = calculateTax({ amount: 100, country: 'DE' });
    expect(result.taxRate).toBe(19);
    expect(result.type).toBe('VAT');
    expect(result.taxAmount).toBe(19);
    expect(result.total).toBe(119);
    // EU VAT is treated as already included in the displayed price
    expect(result.isInclusive).toBe(true);
  });

  it('treats UK VAT as exclusive (post-Brexit pricing)', () => {
    const result = calculateTax({ amount: 100, country: 'GB' });
    expect(result.taxRate).toBe(20);
    expect(result.isInclusive).toBe(false);
  });

  it('applies a sub-1 rate correctly for Switzerland', () => {
    const result = calculateTax({ amount: 100, country: 'CH' });
    expect(result.taxRate).toBe(7.7);
    expect(result.taxAmount).toBe(7.7);
  });

  it('handles a zero-tax country', () => {
    const result = calculateTax({ amount: 250, country: 'KW' });
    expect(result.taxRate).toBe(0);
    expect(result.taxAmount).toBe(0);
    expect(result.total).toBe(250);
  });

  it('applies US state sales tax when a state is supplied', () => {
    const result = calculateTax({ amount: 100, country: 'US', state: 'CA' });
    expect(result.taxRate).toBe(7.25);
    expect(result.type).toBe('Sales Tax');
    expect(result.taxAmount).toBe(7.25);
    expect(result.state).toBe('CA');
  });

  it('accepts a lowercase state code', () => {
    expect(calculateTax({ amount: 100, country: 'US', state: 'ny' }).taxRate).toBe(4);
  });

  it('falls back to zero for an unknown US state', () => {
    expect(calculateTax({ amount: 100, country: 'US', state: 'ZZ' }).taxRate).toBe(0);
  });

  it('uses the country rate when US is given without a state', () => {
    const result = calculateTax({ amount: 100, country: 'US' });
    expect(result.taxRate).toBe(0);
    expect(result.state).toBeNull();
  });

  it('returns UNKNOWN type for an unsupported country', () => {
    const result = calculateTax({ amount: 100, country: 'ZZ' });
    expect(result.type).toBe('UNKNOWN');
    expect(result.taxAmount).toBe(0);
  });

  it('rounds monetary values to 2 decimals and keeps the breakdown consistent', () => {
    const result = calculateTax({ amount: 19.99, country: 'DE' });
    expect(result.taxAmount).toBe(3.8);
    expect(result.total).toBe(23.79);
    expect(result.breakdown).toEqual({ subtotal: 19.99, tax: 3.8, total: 23.79 });
    // breakdown must always agree with the top-level figures
    expect(result.breakdown.total).toBeCloseTo(result.total, 10);
  });

  it('surfaces the note field for countries with a caveat', () => {
    expect(calculateTax({ amount: 100, country: 'IN' }).note).toBe('varies 5-28%');
  });

  it('uppercases the currency on the zero-amount path', () => {
    expect(calculateTax({ amount: 0, country: 'DE', currency: 'eur' }).currency).toBe('EUR');
  });
});

describe('taxCalculator - lookups', () => {
  it('getTaxInfo returns the country entry', () => {
    expect(getTaxInfo('DE')).toMatchObject({ rate: 19, type: 'VAT' });
  });

  it('getTaxInfo returns null for an unknown country', () => {
    expect(getTaxInfo('ZZ')).toBeNull();
  });

  it('getAllTaxRates exposes the whole table', () => {
    const all = getAllTaxRates();
    expect(all.DE.rate).toBe(19);
    expect(Object.keys(all).length).toBeGreaterThan(50);
  });

  it('getUSStateTaxRates exposes 50 states plus DC', () => {
    expect(Object.keys(getUSStateTaxRates()).length).toBe(51);
  });
});

describe('taxCalculator - formatTaxDisplay', () => {
  it('reports "No tax" when the tax amount is zero', () => {
    expect(formatTaxDisplay({ taxAmount: 0 })).toBe('No tax');
  });

  it('formats a non-zero amount with the currency symbol and rate', () => {
    const result = calculateTax({ amount: 100, country: 'DE' });
    expect(formatTaxDisplay(result)).toBe('$19.00 (VAT: 19%)');
  });

  it('honours a custom currency symbol', () => {
    const result = calculateTax({ amount: 100, country: 'DE' });
    expect(formatTaxDisplay(result, '€')).toBe('€19.00 (VAT: 19%)');
  });
});
