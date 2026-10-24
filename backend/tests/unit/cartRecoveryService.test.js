/**
 * Abandoned-cart recovery service tests.
 *
 * Covers the three entry points the CART_RECOVERY worker uses: arming the
 * window (with its stable dedupe job id), disarming it for one user's cart, and
 * the consumer-side evaluation that decides whether to mark a cart abandoned and
 * enqueue the "complete your purchase" email. Every DB read is asserted to carry
 * its filter (cart id / user id / product include) so a query that silently
 * loses a scope cannot pass review.
 */
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

const models = {};

/** Module doubles delegate to the per-test fake so mocked identities stay stable. */
const delegate = (key) =>
  new Proxy(
    {},
    {
      get: (_target, prop) => {
        const model = models[key];
        return model ? model[prop] : undefined;
      },
    },
  );

const queue = {
  enqueueCartRecovery: jest.fn(),
  enqueueEmail: jest.fn(),
};

jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  __esModule: true,
  enqueueCartRecovery: (...args) => queue.enqueueCartRecovery(...args),
  enqueueEmail: (...args) => queue.enqueueEmail(...args),
  QUEUES: { CART_RECOVERY: 'cart-recovery', EMAIL: 'email' },
}));

jest.unstable_mockModule('../../models/Cart.js', () => ({
  __esModule: true,
  default: delegate('Cart'),
}));
jest.unstable_mockModule('../../models/CartItem.js', () => ({
  __esModule: true,
  default: delegate('CartItem'),
}));
jest.unstable_mockModule('../../models/Product.js', () => ({
  __esModule: true,
  default: delegate('Product'),
}));
jest.unstable_mockModule('../../models/User.js', () => ({
  __esModule: true,
  default: delegate('User'),
}));

const { default: Product } = await import('../../models/Product.js');
const recovery = await import('../../services/checkout/recovery.service.js');
const { armCartRecovery, disarmCartRecovery, recoverCart } = recovery;

const TWO_HOURS_MS = 2 * 60 * 60 * 1000;
const inHours = (hours) => new Date(Date.now() + hours * 60 * 60 * 1000);

function seedCart(overrides = {}) {
  const row = {
    id: 1,
    user_id: 7,
    org_id: null,
    expires_at: inHours(-1),
    abandoned_at: null,
    ...overrides,
  };
  models.Cart = createFakeModel('Cart', [row]);
  return row;
}

const seedItems = (items) => {
  models.CartItem = createFakeModel('CartItem', items);
};

const seedUser = (user) => {
  models.User = createFakeModel('User', user ? [user] : []);
};

function freshModels() {
  seedCart();
  seedItems([]);
  seedUser({ id: 7, name: 'Ada', email: 'ada@example.com' });
  models.Product = createFakeModel('Product', [
    { id: 11, title: 'Keyboard', price: '60.00' },
    { id: 12, title: 'Mouse', price: '15.00' },
  ]);
}

beforeEach(() => {
  freshModels();
  process.env.FRONTEND_URL = 'https://shop.test';
  queue.enqueueCartRecovery.mockResolvedValue({ id: 'job-1' });
  queue.enqueueEmail.mockResolvedValue({ id: 'job-2' });
});

afterEach(() => {
  delete process.env.FRONTEND_URL;
});

describe('armCartRecovery', () => {
  it('sets a 2-hour window and clears any previous abandonment', async () => {
    const row = seedCart({ expires_at: null, abandoned_at: new Date() });
    const cart = await models.Cart.findByPk(1);

    const expiresAt = await armCartRecovery(cart);

    expect(row.expires_at).toBeInstanceOf(Date);
    expect(row.abandoned_at).toBeNull();
    const delta = row.expires_at.getTime() - Date.now();
    expect(delta).toBeGreaterThan(TWO_HOURS_MS - 5000);
    expect(delta).toBeLessThanOrEqual(TWO_HOURS_MS);
    expect(expiresAt.getTime()).toBe(row.expires_at.getTime());
  });

  it('schedules the delayed job with the cart owner and the window deadline', async () => {
    const cart = await models.Cart.findByPk(1);

    await armCartRecovery(cart);

    expect(queue.enqueueCartRecovery).toHaveBeenCalledTimes(1);
    const [payload, options] = queue.enqueueCartRecovery.mock.calls[0];
    expect(payload).toEqual({ cartId: 1, userId: 7, expiresAt: cart.expires_at.toISOString() });
    expect(options.delay).toBe(TWO_HOURS_MS);
  });

  it('reuses one job id per cart so re-arming replaces the pending window', async () => {
    const cart = await models.Cart.findByPk(1);

    await armCartRecovery(cart);
    await armCartRecovery(cart);

    const jobIds = queue.enqueueCartRecovery.mock.calls.map(([, options]) => options.jobId);
    expect(jobIds).toEqual(['cart-recovery-1', 'cart-recovery-1']);
  });
});

describe('disarmCartRecovery', () => {
  it("clears the window only for that user's cart", async () => {
    const row = seedCart();

    await disarmCartRecovery(7);

    expect(row.expires_at).toBeNull();
    expect(row.abandoned_at).toBeNull();
    const call = models.Cart.calls.find((c) => c.method === 'update');
    // createFakeModel.update records `{ values, options }` under `options`.
    expect(call.options.options).toEqual({ where: { user_id: 7 } });
    expect(call.options.values).toEqual({ expires_at: null, abandoned_at: null });
  });

  it('does not clear another user cart', async () => {
    const row = seedCart({ user_id: 7 });

    await disarmCartRecovery(99);

    expect(row.expires_at).toBeInstanceOf(Date);
  });
});

describe('recoverCart — skip paths', () => {
  it('skips a cart that no longer exists', async () => {
    seedCart();

    const result = await recoverCart(999);

    expect(result).toEqual({ skipped: true, reason: 'cart-gone' });
    expect(queue.enqueueEmail).not.toHaveBeenCalled();
  });

  it('skips a cart that was already marked abandoned and never re-emails', async () => {
    const flaggedAt = inHours(-2);
    const row = seedCart({ abandoned_at: flaggedAt });
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 2, price: '60.00' }]);

    const result = await recoverCart(1);

    expect(result).toEqual({ skipped: true, reason: 'already-abandoned' });
    expect(queue.enqueueEmail).not.toHaveBeenCalled();
    expect(row.abandoned_at.getTime()).toBe(flaggedAt.getTime());
    expect(models.CartItem.calls).toEqual([]);
  });

  it('skips a cart whose window has not lapsed yet', async () => {
    const row = seedCart({ expires_at: inHours(1) });

    const result = await recoverCart(1);

    expect(result).toEqual({ skipped: true, reason: 'not-yet-expired' });
    expect(row.abandoned_at).toBeNull();
  });

  it('skips a cart with no armed window', async () => {
    const row = seedCart({ expires_at: null });

    const result = await recoverCart(1);

    expect(result).toEqual({ skipped: true, reason: 'not-yet-expired' });
    expect(row.abandoned_at).toBeNull();
  });

  it('skips an emptied cart and leaves it un-flagged', async () => {
    const row = seedCart();
    seedItems([]);

    const result = await recoverCart(1);

    expect(result).toEqual({ skipped: true, reason: 'empty-cart' });
    expect(row.abandoned_at).toBeNull();
    expect(queue.enqueueEmail).not.toHaveBeenCalled();
  });
});

describe('recoverCart — abandonment + email', () => {
  it('marks the cart abandoned and emails the owner once', async () => {
    const row = seedCart();
    seedItems([
      { id: 1, cart_id: 1, product_id: 11, quantity: 2, price: '60.00' },
      { id: 2, cart_id: 1, product_id: 12, quantity: 1, price: '15.00' },
    ]);

    const result = await recoverCart(1);

    expect(result).toEqual({ skipped: false });
    expect(row.abandoned_at).toBeInstanceOf(Date);
    expect(queue.enqueueEmail).toHaveBeenCalledTimes(1);
    const mail = queue.enqueueEmail.mock.calls[0][0];
    expect(mail.to).toBe('ada@example.com');
    expect(mail.subject).toBe('Your cart is waiting — 2 item(s) ready');
    expect(mail.html).toContain('Hi Ada, your cart is waiting');
    expect(mail.html).toContain('Complete your order');
    expect(mail.html).toContain('Subtotal: $135.00');
  });

  it('scopes the item query to this cart and eager-loads the product', async () => {
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 1, price: '10.00' }]);

    await recoverCart(1);

    const call = models.CartItem.whereCalls('findAll')[0];
    expect(call.where).toEqual({ cart_id: 1 });
    expect(call.include).toEqual([{ model: Product, as: 'product' }]);
  });

  it('ignores items belonging to a different cart', async () => {
    seedItems([{ id: 1, cart_id: 42, product_id: 11, quantity: 1, price: '10.00' }]);

    const result = await recoverCart(1);

    expect(result).toEqual({ skipped: true, reason: 'empty-cart' });
  });

  it('marks the cart abandoned without emailing when the user has no address', async () => {
    const row = seedCart();
    seedUser({ id: 7, name: 'Ada', email: null });
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 1, price: '10.00' }]);

    const result = await recoverCart(1);

    expect(result).toEqual({ skipped: false });
    expect(row.abandoned_at).toBeInstanceOf(Date);
    expect(queue.enqueueEmail).not.toHaveBeenCalled();
  });

  it('marks the cart abandoned without throwing when the user row is gone', async () => {
    const row = seedCart();
    seedUser(null);
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 1, price: '10.00' }]);

    await expect(recoverCart(1)).resolves.toEqual({ skipped: false });
    expect(row.abandoned_at).toBeInstanceOf(Date);
    expect(queue.enqueueEmail).not.toHaveBeenCalled();
  });

  it('falls back to the email address when the user has no display name', async () => {
    seedUser({ id: 7, name: null, email: 'ada@example.com' });
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 1, price: '10.00' }]);

    await recoverCart(1);

    expect(queue.enqueueEmail.mock.calls[0][0].html).toContain('Hi ada@example.com,');
  });

  it('links the CTA to the configured storefront', async () => {
    process.env.FRONTEND_URL = 'https://brand.example';
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 1, price: '10.00' }]);

    await recoverCart(1);

    expect(queue.enqueueEmail.mock.calls[0][0].html).toContain('href="https://brand.example/checkout"');
  });

  it('does not double the slash when the storefront origin ends in one', async () => {
    process.env.FRONTEND_URL = 'https://brand.example/';
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 1, price: '10.00' }]);

    await recoverCart(1);

    const html = queue.enqueueEmail.mock.calls[0][0].html;
    expect(html).toContain('href="https://brand.example/checkout"');
    expect(html).not.toContain('//checkout');
  });

  it('defaults the CTA link to the local dev storefront', async () => {
    delete process.env.FRONTEND_URL;
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 1, price: '10.00' }]);

    await recoverCart(1);

    expect(queue.enqueueEmail.mock.calls[0][0].html).toContain(
      'href="http://localhost:5173/checkout"',
    );
  });
});

/* ══════════════════════════════════════════════════════════════════════
 * Regression guards — defects found by this suite, fixed in the service.
 * ══════════════════════════════════════════════════════════════════════ */

describe('recovery.service — pricing and queue-failure guards', () => {
  it('prices a recovered line from the eager-loaded product', async () => {
    // models/CartItem.js has no price column, so every real row arrived here
    // without one; the joined product is the only price source.
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 2 }]);

    await recoverCart(1);

    const html = queue.enqueueEmail.mock.calls[0][0].html;
    expect(html).not.toContain('NaN');
    expect(html).toContain('Keyboard × 2');
    expect(html).toContain('$120.00');
    expect(html).toContain('Subtotal: $120.00');
  });

  it('prefers the stored line price over the product price', async () => {
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 2, price: '55.00' }]);

    await recoverCart(1);

    expect(queue.enqueueEmail.mock.calls[0][0].html).toContain('Subtotal: $110.00');
  });

  it('prices a line at zero instead of NaN when the product row is gone', async () => {
    seedItems([{ id: 1, cart_id: 1, product_id: 99, quantity: 3 }]);

    await recoverCart(1);

    const html = queue.enqueueEmail.mock.calls[0][0].html;
    expect(html).not.toContain('NaN');
    expect(html).toContain('Item × 3');
    expect(html).toContain('Subtotal: $0.00');
  });

  it('leaves the cart un-flagged when the email enqueue fails so the job retries', async () => {
    const row = seedCart();
    seedItems([{ id: 1, cart_id: 1, product_id: 11, quantity: 1, price: '60.00' }]);
    queue.enqueueEmail.mockRejectedValue(new Error('redis queue down'));

    // The failure must propagate: swallowing it committed the abandonment and the
    // buyer was never mailed for that cart again.
    await expect(recoverCart(1)).rejects.toThrow('redis queue down');

    expect(row.abandoned_at).toBeNull();
  });
});
