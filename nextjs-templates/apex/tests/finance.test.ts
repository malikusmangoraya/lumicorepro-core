import { describe, expect, it } from 'vitest';
import { calculateFinance } from '@/lib/finance';

const base = { price: 100_000, deposit: 10_000, aprPercent: 6.9, termMonths: 48 };

describe('calculateFinance', () => {
  it('finances the price minus the deposit', () => {
    expect(calculateFinance(base).financed).toBe(90_000);
  });

  it('handles a 0% offer without dividing by zero', () => {
    const result = calculateFinance({ ...base, aprPercent: 0 });
    expect(result.monthly).toBe(1875);
    expect(result.totalInterest).toBe(0);
  });

  it('charges more interest at a higher rate', () => {
    const low = calculateFinance({ ...base, aprPercent: 3.9 });
    const high = calculateFinance({ ...base, aprPercent: 12.9 });
    expect(high.monthly).toBeGreaterThan(low.monthly);
    expect(high.totalInterest).toBeGreaterThan(low.totalInterest);
  });

  it('lowers the payment as the term lengthens', () => {
    const short = calculateFinance({ ...base, termMonths: 24 });
    const long = calculateFinance({ ...base, termMonths: 72 });
    expect(long.monthly).toBeLessThan(short.monthly);
    // A longer term costs more overall even though each payment is smaller.
    expect(long.totalInterest).toBeGreaterThan(short.totalInterest);
  });

  it('lowers the payment as the deposit grows', () => {
    const small = calculateFinance({ ...base, deposit: 5_000 });
    const large = calculateFinance({ ...base, deposit: 30_000 });
    expect(large.monthly).toBeLessThan(small.monthly);
  });

  it('never finances more than the price', () => {
    const result = calculateFinance({ ...base, deposit: 999_999 });
    expect(result.financed).toBe(0);
    expect(Number.isFinite(result.monthly)).toBe(true);
  });

  it('clamps a nonsense term instead of dividing by zero', () => {
    const result = calculateFinance({ ...base, termMonths: 0 });
    expect(Number.isFinite(result.monthly)).toBe(true);
    expect(result.monthly).toBeGreaterThan(0);
  });

  it('reports the total payable including the deposit', () => {
    const result = calculateFinance(base);
    expect(result.totalPayable).toBeCloseTo(result.monthly * base.termMonths + base.deposit, 0);
  });
});
