/**
 * Abandoned-Checkout Recovery
 * ---------------------------
 * Arms a 2-hour recovery window whenever a cart shows checkout intent (item
 * added/updated). The delayed CART_RECOVERY job re-checks the cart when the
 * window lapses: if it still holds items and no order replaced it, the cart is
 * marked abandoned and a "complete your purchase" email is enqueued. Deduped
 * via a stable job id so re-arming simply reschedules the window.
 */
import Cart from '../../models/Cart.js';
import CartItem from '../../models/CartItem.js';
import Product from '../../models/Product.js';
import User from '../../models/User.js';
import { enqueueCartRecovery, enqueueEmail } from '../queue/queue.service.js';

const RECOVERY_DELAY_MS = 2 * 60 * 60 * 1000; // 2h
const RECOVERY_URL = '/checkout';

/** Discovery link helper kept local so links stay constructor-free. */
function recoveryLink() {
  const origin = process.env.FRONTEND_URL || 'http://localhost:5173';
  return `${origin}${RECOVERY_URL}`;
}

/**
 * Arm (or re-arm) the recovery window for a cart after checkout-intent signal.
 * Replaces any previously scheduled job; a completed order disarms instead.
 */
export async function armCartRecovery(cart) {
  const expiresAt = new Date(Date.now() + RECOVERY_DELAY_MS);
  await cart.update({ expires_at: expiresAt, abandoned_at: null });
  await enqueueCartRecovery(
    { cartId: cart.id, userId: cart.user_id, expiresAt: expiresAt.toISOString() },
    { delay: RECOVERY_DELAY_MS, jobId: `cart-recovery-${cart.id}` }
  );
  return expiresAt;
}

/** Cancel the recovery window once the cart is emptied or converted to an order. */
export async function disarmCartRecovery(userId) {
  await Cart.update({ expires_at: null, abandoned_at: null }, { where: { user_id: userId } });
}

/**
 * Consumer-side evaluation: called by the delayed CART_RECOVERY job.
 * Marks the cart abandoned and enqueues the recovery email.
 */
export async function recoverCart(cartId) {
  const cart = await Cart.findByPk(cartId);
  if (!cart) return { skipped: true, reason: 'cart-gone' };
  if (cart.abandoned_at) return { skipped: true, reason: 'already-abandoned' };
  if (!cart.expires_at || new Date(cart.expires_at) > new Date()) {
    return { skipped: true, reason: 'not-yet-expired' };
  }

  const items = await CartItem.findAll({
    where: { cart_id: cart.id },
    include: [{ model: Product, as: 'product' }],
  });
  if (!items.length) return { skipped: true, reason: 'empty-cart' };

  const user = await User.findByPk(cart.user_id);
  await cart.update({ abandoned_at: new Date() });

  if (user?.email) {
    const subtotal = items.reduce(
      (sum, it) => sum + parseFloat(it.price || 0) * it.quantity,
      0
    );
    await enqueueEmail({
      to: user.email,
      subject: `Your cart is waiting — ${items.length} item(s) ready`,
      html: recoveryEmailHtml(user.name || user.email, items, subtotal),
    });
  }

  return { skipped: false };
}

function recoveryEmailHtml(name, items, subtotal) {
  const rows = items
    .map((it) => {
      const title = it.product?.title || it.title || 'Item';
      const line = `${title} × ${it.quantity}`;
      const price = `$${(parseFloat(it.price) * it.quantity).toFixed(2)}`;
      return `<tr><td style="padding:8px 0;border-bottom:1px solid #eee">${line}</td><td style="padding:8px 0;border-bottom:1px solid #eee;text-align:right">${price}</td></tr>`;
    })
    .join('');
  const link = recoveryLink();
  return `
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto">
      <h2>Hi ${name}, your cart is waiting</h2>
      <p>You started a checkout but didn't finish. Your items are still reserved:</p>
      <table style="width:100%;border-collapse:collapse">${rows}</table>
      <p style="font-size:18px"><strong>Subtotal: $${subtotal.toFixed(2)}</strong></p>
      <p><a href="${link}" style="background:#2563eb;color:#fff;padding:12px 20px;border-radius:6px;text-decoration:none;display:inline-block">Complete your order</a></p>
    </div>`;
}

export default { armCartRecovery, disarmCartRecovery, recoverCart };