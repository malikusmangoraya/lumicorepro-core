/**
 * Which product line an order belongs to. The `orders` table is shared by every
 * vertical, so a per-vertical listing or admin mutation has to filter on this
 * column or a restaurant dashboard can read — and rewrite — store orders.
 *
 * Lives here rather than in `models/Order.js` because the service validates it
 * too, and feature tests mock the model module without mocking this one.
 */
export const ORDER_SOURCES = ['ecommerce', 'restaurant'];
