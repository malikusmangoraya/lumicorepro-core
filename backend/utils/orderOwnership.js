/**
 * Ownership guard for order-scoped endpoints.
 *
 * Any route that accepts an `orderId` from the client and acts on that order
 * must verify the authenticated user owns it (or is an admin). Without this,
 * one user can drive payment sessions against another user's order (IDOR) —
 * the exact bug fixed in payment.routes.js for create-intent, paypal/create-order,
 * paddle/checkout and stripe checkout.
 *
 * Returns null when access is allowed, or `{ status, error }` otherwise.
 */
export function orderOwnershipError(order, user) {
  if (!order) return { status: 404, error: 'Order not found' };
  if (user?.role !== 'admin' && String(order.user_id) !== String(user?.id)) {
    return { status: 403, error: 'Not authorized for this order' };
  }
  return null;
}

export default { orderOwnershipError };
