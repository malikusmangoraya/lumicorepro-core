/**
 * Unit tests — middleware/validateRequest.js + middleware/validations/*.js
 *
 * Why this file exists: routes/order.routes.js:129,182 (and
 * routes/auth.routes.js:131,241) wire `validateRequest(schema)` exactly as the
 * helper documents, but the helper used to read `{ body, query, params }` off the
 * schema object itself. On the installed Zod those keys live on `schema.shape`,
 * so every destructure yielded `undefined` and each of those four endpoints was a
 * silent pass-through — it looked validated and was not.
 *
 * `validateRequest` now accepts both wirings, and these tests pin the outcome:
 * an invalid body answers 422 with the canonical envelope and never reaches the
 * handler, and a valid body is replaced by the parsed one so unknown client keys
 * are stripped before the handler reads them.
 */
import { describe, it, expect } from '@jest/globals';
import { z } from 'zod';
import { validateRequest } from '../../middleware/validateRequest.js';
import { createOrderSchema, updateOrderStatusSchema } from '../../middleware/validations/order.schema.js';
import { registerSchema, loginSchema } from '../../middleware/validations/auth.schema.js';

/** Minimal Express response double. */
const createRes = () => {
  const res = { statusCode: 0, body: null, headersSent: false };
  res.status = (code) => {
    res.statusCode = code;
    return res;
  };
  res.json = (body) => {
    res.body = body;
    res.headersSent = true;
    return res;
  };
  return res;
};

/** Run a middleware and report what it did. */
const run = (middleware, req) => {
  const res = createRes();
  let nextCalled = false;
  middleware(req, res, () => {
    nextCalled = true;
  });
  return { res, nextCalled };
};

const validate = (schema, req) => run(validateRequest(schema), req);

/** A checkout body in the shape `createOrder` reads: catalog ids, client prices gone. */
const validBody = () => ({
  items: [{ product: 100, quantity: 2 }],
  shippingAddress: { street: '1 Main St', city: 'New York', state: 'NY', country: 'US', zipCode: '10001' },
  paymentMethod: 'stripe',
});

describe('Zod schema shape access (root cause)', () => {
  it('keeps the declared keys on `.shape`, not on the schema instance', () => {
    expect(z.object({ body: z.object({ a: z.string() }) }).body).toBeUndefined();
    expect(createOrderSchema.body).toBeUndefined();
    expect(createOrderSchema.query).toBeUndefined();
    expect(createOrderSchema.params).toBeUndefined();
    expect(typeof createOrderSchema.shape.body.parse).toBe('function');
  });

  it('reads the parts from a Zod schema and from a plain object literal alike', () => {
    const empty = { body: {}, query: {}, params: {} };

    // The route-side wiring and the explicit `.shape` wiring must not diverge.
    expect(validate(createOrderSchema, { ...empty }).nextCalled).toBe(
      validate(createOrderSchema.shape, { ...empty }).nextCalled
    );
    expect(validate({ body: z.object({ a: z.string() }) }, { body: {}, query: {}, params: {} }).res.statusCode).toBe(422);
  });
});

describe('validateRequest(schema) — the wiring every route uses', () => {
  it('rejects an order body with no items, address or payment method', () => {
    const { res, nextCalled } = validate(createOrderSchema, { body: {}, query: {}, params: {} });

    expect(nextCalled).toBe(false);
    expect(res.statusCode).toBe(422);
    expect(res.body).toMatchObject({
      success: false,
      status: 422,
      message: 'Validation failed',
      code: 'VALIDATION_ERROR',
      data: null,
    });
    expect(res.body.details.map((d) => d.path)).toEqual(
      expect.arrayContaining(['items', 'shippingAddress', 'paymentMethod'])
    );
  });

  it('coerces defaults and strips keys the service must never read', () => {
    const req = {
      body: {
        ...validBody(),
        notes: undefined,
        isAdmin: true,
        items: [{ product: 100, quantity: 2, price: 0.01, title: 'Forged', image: 'https://evil.test/x.png' }],
      },
      query: {},
      params: {},
    };
    const { res, nextCalled } = validate(createOrderSchema, req);

    expect(nextCalled).toBe(true);
    expect(res.statusCode).toBe(0);
    expect(req.body.notes).toBe('');
    expect(req.body.isAdmin).toBeUndefined();
    expect(req.body.items[0]).toEqual({ product: 100, quantity: 2 });
  });

  it('reports the offending line path, not just the array', () => {
    const { res } = validate(createOrderSchema, {
      body: { ...validBody(), items: [{ product: -1, quantity: 0 }] },
      query: {},
      params: {},
    });

    expect(res.statusCode).toBe(422);
    expect(res.body.details.map((d) => d.path)).toEqual(
      expect.arrayContaining(['items.0.product', 'items.0.quantity'])
    );
  });

  it('enforces the order-status enum and the numeric-id param guard', () => {
    const badStatus = validate(updateOrderStatusSchema, {
      body: { status: 'teleported' },
      query: {},
      params: { id: '1' },
    });
    const badParam = validate(updateOrderStatusSchema, {
      body: { status: 'shipped' },
      query: {},
      params: { id: 'not-a-number' },
    });

    expect(badStatus.nextCalled).toBe(false);
    expect(badStatus.res.body.details).toEqual([
      { path: 'status', message: expect.stringContaining('Invalid option') },
    ]);
    expect(badParam.res.statusCode).toBe(422);
    expect(badParam.res.body.details).toEqual([{ path: 'id', message: 'Order ID must be a number' }]);
  });

  it('validates the auth bodies too, so the blast radius stays closed', () => {
    const noCredentials = validate(registerSchema, { body: {}, query: {}, params: {} });
    const shortPassword = validate(loginSchema, {
      body: { email: 'not-an-email', password: '' },
      query: {},
      params: {},
    });

    expect(noCredentials.nextCalled).toBe(false);
    expect(noCredentials.res.statusCode).toBe(422);
    expect(shortPassword.nextCalled).toBe(false);
    expect(shortPassword.res.body.details.map((d) => d.path)).toEqual(
      expect.arrayContaining(['email', 'password'])
    );
  });
});

describe('validateRequest failure modes', () => {
  it('returns the 500 envelope when a schema throws something that is not a ZodError', () => {
    const explosive = { parse() { throw new TypeError('schema bug'); } };
    const { res, nextCalled } = validate({ body: explosive }, { body: {}, query: {}, params: {} });

    expect(nextCalled).toBe(false);
    expect(res.statusCode).toBe(500);
    expect(res.body).toMatchObject({
      success: false,
      status: 500,
      code: 'INTERNAL_ERROR',
      message: 'Validation middleware error',
      data: null,
    });
    expect(typeof res.body.timestamp).toBe('string');
  });

  it('passes straight through when no schema is supplied at all', () => {
    const { nextCalled } = validate(undefined, { body: { anything: true }, query: {}, params: {} });
    expect(nextCalled).toBe(true);
  });
});
