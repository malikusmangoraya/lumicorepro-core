import { describe, it, expect } from '@jest/globals';
import { orderOwnershipError } from '../../utils/orderOwnership.js';

/**
 * Regression: payment routes (create-intent, paypal/create-order,
 * paddle/checkout, stripe checkout) used to accept any orderId from an
 * authenticated client without verifying ownership — an IDOR that let one user
 * drive payment sessions against another user's order. Every order-scoped route
 * must call this guard.
 */
describe('orderOwnershipError', () => {
  it('allows the order owner', () => {
    expect(orderOwnershipError({ id: 5, user_id: 42 }, { id: 42, role: 'user' })).toBeNull();
  });

  it('coerces numeric/string ids before comparing', () => {
    expect(orderOwnershipError({ id: 5, user_id: '42' }, { id: 42 })).toBeNull();
    expect(orderOwnershipError({ id: 5, user_id: 42 }, { id: '42' })).toBeNull();
  });

  it('blocks a different user with 403', () => {
    const err = orderOwnershipError({ id: 5, user_id: 42 }, { id: 7, role: 'user' });
    expect(err).toEqual({ status: 403, error: 'Not authorized for this order' });
  });

  it('lets admins act on any order', () => {
    expect(orderOwnershipError({ id: 5, user_id: 42 }, { id: 7, role: 'admin' })).toBeNull();
  });

  it('returns 404 for a missing order', () => {
    expect(orderOwnershipError(null, { id: 42 })).toEqual({ status: 404, error: 'Order not found' });
  });

  it('blocks anonymous callers (no user) on an existing order', () => {
    const err = orderOwnershipError({ id: 5, user_id: 42 }, undefined);
    expect(err?.status).toBe(403);
  });
});
