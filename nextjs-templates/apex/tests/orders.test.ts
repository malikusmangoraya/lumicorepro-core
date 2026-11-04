import { describe, expect, it } from 'vitest';
import {
  calculateTotals,
  canTransition,
  isTerminal,
  nextStatuses,
  primaryAction,
  requiresTracking,
} from '@/lib/orders';

describe('order transitions', () => {
  it('walks the happy path', () => {
    expect(canTransition('pending', 'paid')).toBe(true);
    expect(canTransition('paid', 'processing')).toBe(true);
    expect(canTransition('processing', 'shipped')).toBe(true);
    expect(canTransition('shipped', 'delivered')).toBe(true);
  });

  it('refuses to skip a step', () => {
    expect(canTransition('pending', 'shipped')).toBe(false);
    expect(canTransition('paid', 'delivered')).toBe(false);
  });

  it('refuses to revive a terminal order', () => {
    for (const from of ['delivered', 'cancelled', 'refunded']) {
      expect(canTransition(from, 'processing')).toBe(false);
      expect(isTerminal(from)).toBe(true);
    }
  });

  it('refuses a no-op transition', () => {
    expect(canTransition('paid', 'paid')).toBe(false);
  });

  it('allows a refund after delivery but not before payment', () => {
    expect(canTransition('delivered', 'refunded')).toBe(true);
    expect(canTransition('pending', 'refunded')).toBe(false);
  });

  it('lists what is reachable', () => {
    expect(nextStatuses('pending')).toEqual(['paid', 'cancelled']);
    expect(nextStatuses('delivered')).toEqual(['refunded']);
    expect(nextStatuses('nonsense')).toEqual([]);
  });

  it('requires tracking only for shipped and delivered', () => {
    expect(requiresTracking('shipped')).toBe(true);
    expect(requiresTracking('delivered')).toBe(true);
    expect(requiresTracking('processing')).toBe(false);
  });

  it('suggests the next action', () => {
    expect(primaryAction('pending')).toEqual({ to: 'paid', label: 'Mark paid' });
    expect(primaryAction('delivered')).toBeNull();
  });
});

describe('calculateTotals', () => {
  it('multiplies price by quantity and rounds to cents', () => {
    const totals = calculateTotals([{ unitPrice: 19.99, quantity: 3 }]);
    expect(totals.subtotal).toBe(59.97);
    expect(totals.total).toBe(59.97);
  });

  it('caps the discount at the subtotal', () => {
    const totals = calculateTotals([{ unitPrice: 100, quantity: 1 }], { discount: 500 });
    expect(totals.discount).toBe(100);
    expect(totals.total).toBe(0);
  });

  it('applies tax after the discount', () => {
    const totals = calculateTotals([{ unitPrice: 100, quantity: 1 }], {
      discount: 20,
      taxRate: 0.2,
      shipping: 10,
    });
    expect(totals.tax).toBe(16);
    expect(totals.total).toBe(106);
  });

  it('ignores negative quantities and prices', () => {
    const totals = calculateTotals([{ unitPrice: -50, quantity: 2 }, { unitPrice: 10, quantity: 1 }]);
    expect(totals.subtotal).toBe(10);
  });
});
