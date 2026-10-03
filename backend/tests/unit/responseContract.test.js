import { describe, it, expect, jest } from '@jest/globals';
import resp, { ok, created, fail, sendSuccess, sendError } from '../../utils/response.js';

/**
 * Canonical response envelope contract (AGENTS.md §4).
 *
 *   success → { success, status, message, data, timestamp }
 *   error   → { success: false, status, message, code, data: null, timestamp }
 *
 * These assertions pin the EXACT key set so an accidental extra/renamed key
 * (or a dropped `timestamp`) fails the build instead of silently changing the
 * public API contract.
 */

const SUCCESS_KEYS = ['success', 'status', 'message', 'data', 'timestamp'];
const ERROR_KEYS = ['success', 'status', 'message', 'code', 'data', 'timestamp'];

const fakeRes = () => {
  const res = { headersSent: false };
  res.status = jest.fn((code) => {
    res._status = code;
    res.statusCode = code;
    return res;
  });
  res.json = jest.fn((body) => {
    res._body = body;
    res.headersSent = true;
    return res;
  });
  return res;
};

const sortedKeys = (body) => Object.keys(body).sort();
const sorted = (keys) => [...keys].sort();

describe('Canonical envelope: success bodies', () => {
  it('ok() emits exactly the canonical success key set', () => {
    const res = fakeRes();
    ok(res, { id: 7, name: 'Order' });

    expect(sortedKeys(res._body)).toEqual(sorted(SUCCESS_KEYS));
    expect(res._body).toMatchObject({ success: true, status: 200, data: { id: 7, name: 'Order' } });
    expect(typeof res._body.message).toBe('string');
    expect(res._body.message.length).toBeGreaterThan(0);
  });

  it('success bodies carry an ISO timestamp that parses as a date', () => {
    const res = fakeRes();
    ok(res, null);

    expect(typeof res._body.timestamp).toBe('string');
    expect(Number.isNaN(Date.parse(res._body.timestamp))).toBe(false);
    expect(new Date(res._body.timestamp).toISOString()).toBe(res._body.timestamp);
  });

  it('status always matches the HTTP status actually used', () => {
    const ok200 = fakeRes();
    ok(ok200, []);
    expect(ok200._status).toBe(200);
    expect(ok200._body.status).toBe(ok200._status);

    const created201 = fakeRes();
    created(created201, { id: 1 });
    expect(created201._status).toBe(201);
    expect(created201._body.status).toBe(created201._status);
    expect(sortedKeys(created201._body)).toEqual(sorted(SUCCESS_KEYS));

    const accepted202 = fakeRes();
    ok(accepted202, { queued: true }, undefined, 202);
    expect(accepted202._status).toBe(202);
    expect(accepted202._body.status).toBe(202);
  });

  it('data is nullable and defaults to null', () => {
    const res = fakeRes();
    ok(res);
    expect(res._body.data).toBeNull();
  });

  it('meta is additive only when a caller passes it (legacy 3rd arg)', () => {
    const withMeta = fakeRes();
    ok(withMeta, [], { page: 1, total: 50 });
    expect(sortedKeys(withMeta._body)).toEqual([...SUCCESS_KEYS, 'meta'].sort());

    const withoutMeta = fakeRes();
    ok(withoutMeta, [], undefined);
    expect(sortedKeys(withoutMeta._body)).toEqual(sorted(SUCCESS_KEYS));
  });
});

describe('Canonical envelope: error bodies', () => {
  it('fail() emits exactly the canonical error key set', () => {
    const res = fakeRes();
    fail(res, 'VALIDATION_ERROR', 'Bad input', 422);

    expect(sortedKeys(res._body)).toEqual(sorted(ERROR_KEYS));
    expect(res._status).toBe(422);
    expect(res._body).toEqual({
      success: false,
      status: 422,
      message: 'Bad input',
      code: 'VALIDATION_ERROR',
      data: null,
      timestamp: expect.any(String),
    });
  });

  it('error timestamp parses as a date and status matches the HTTP status', () => {
    const res = fakeRes();
    fail(res, 'NOT_FOUND', 'Order not found', 404);

    expect(Number.isNaN(Date.parse(res._body.timestamp))).toBe(false);
    expect(res._body.status).toBe(res._status);
    expect(res._body.status).toBe(404);
    expect(res._body.data).toBeNull();
  });

  it('details is additive only when supplied', () => {
    const withDetails = fakeRes();
    fail(withDetails, 'VALIDATION_ERROR', 'Validation failed', 422, [{ path: 'email' }]);
    expect(sortedKeys(withDetails._body)).toEqual([...ERROR_KEYS, 'details'].sort());

    const withoutDetails = fakeRes();
    fail(withoutDetails, 'VALIDATION_ERROR', 'Validation failed', 422, null);
    expect(sortedKeys(withoutDetails._body)).toEqual(sorted(ERROR_KEYS));
  });

  it('defaults to HTTP 400', () => {
    const res = fakeRes();
    fail(res, 'BAD_REQUEST', 'nope');
    expect(res._status).toBe(400);
    expect(res._body.status).toBe(400);
  });
});

describe('Backwards-compatible aliases', () => {
  it('sendSuccess is the ok() helper', () => {
    const res = fakeRes();
    resp.sendSuccess(res, { id: 2 }, null, 201);
    expect(sortedKeys(res._body)).toEqual(sorted(SUCCESS_KEYS));
    expect(res._status).toBe(201);
    expect(res._body.data).toEqual({ id: 2 });
    expect(sendSuccess).toBe(ok);
  });

  it('sendError is the fail() helper', () => {
    const res = fakeRes();
    resp.sendError(res, 'FORBIDDEN', 'no', 403);
    expect(sortedKeys(res._body)).toEqual(sorted(ERROR_KEYS));
    expect(res._status).toBe(403);
    expect(res._body.code).toBe('FORBIDDEN');
    expect(sendError).toBe(fail);
  });

  it('sendNotFound / sendUnauthorized / sendForbidden / sendServerError keep their codes', () => {
    const notFound = fakeRes();
    resp.sendNotFound(notFound, 'Order');
    expect(notFound._status).toBe(404);
    expect(notFound._body.code).toBe('NOT_FOUND');
    expect(notFound._body.message).toContain('Order');

    const unauth = fakeRes();
    resp.sendUnauthorized(unauth);
    expect(unauth._status).toBe(401);
    expect(unauth._body.code).toBe('UNAUTHORIZED');

    const forbidden = fakeRes();
    resp.sendForbidden(forbidden);
    expect(forbidden._status).toBe(403);
    expect(forbidden._body.code).toBe('FORBIDDEN');

    const server = fakeRes();
    resp.sendServerError(server);
    expect(server._status).toBe(500);
    expect(server._body.code).toBe('INTERNAL_ERROR');

    const validation = fakeRes();
    resp.sendValidationError(validation, [{ path: 'email' }]);
    expect(validation._status).toBe(422);
    expect(validation._body.code).toBe('VALIDATION_ERROR');
  });
});

describe('Exactly one response per request', () => {
  it('never writes a second body once headers have been sent', () => {
    const res = fakeRes();
    ok(res, { first: true });
    expect(res.json).toHaveBeenCalledTimes(1);

    ok(res, { second: true });
    fail(res, 'TOO_LATE', 'already sent', 500);

    expect(res.json).toHaveBeenCalledTimes(1);
    expect(res._body.data).toEqual({ first: true });
  });
});
