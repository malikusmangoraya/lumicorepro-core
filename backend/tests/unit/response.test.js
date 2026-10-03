import { describe, it, expect, jest } from '@jest/globals';
import resp from '../../utils/response.js';

// Minimal express res mock
const fakeRes = () => {
  const res = { headersSent: false };
  res.status = jest.fn((c) => { res._status = c; return res; });
  res.json = jest.fn((b) => { res._body = b; res.headersSent = true; return res; });
  return res;
};

describe('Response wrapper (canonical envelope)', () => {
  it('sendSuccess returns the canonical success envelope', () => {
    const res = fakeRes();
    resp.sendSuccess(res, { id: 1 });
    expect(res._status).toBe(200);
    expect(res._body).toMatchObject({ success: true, status: 200, data: { id: 1 } });
    expect(Object.keys(res._body).sort()).toEqual(
      ['success', 'status', 'message', 'data', 'timestamp'].sort(),
    );
  });

  it('sendSuccess attaches meta when provided', () => {
    const res = fakeRes();
    resp.sendSuccess(res, [], { page: 1, total: 50 }, 200);
    expect(res._body.meta).toEqual({ page: 1, total: 50 });
  });

  it('sendSuccess honours a custom status code', () => {
    const res = fakeRes();
    resp.sendSuccess(res, { id: 3 }, null, 201);
    expect(res._status).toBe(201);
    expect(res._body.status).toBe(201);
  });

  it('sendError returns the canonical error envelope', () => {
    const res = fakeRes();
    resp.sendError(res, 'VALIDATION_ERROR', 'Bad input', 422);
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

  it('sendNotFound uses NOT_FOUND code and 404', () => {
    const res = fakeRes();
    resp.sendNotFound(res, 'Order');
    expect(res._status).toBe(404);
    expect(res._body.code).toBe('NOT_FOUND');
    expect(res._body.message).toContain('Order');
  });

  it('sendUnauthorized / sendForbidden use 401/403', () => {
    const res1 = fakeRes();
    resp.sendUnauthorized(res1);
    expect(res1._status).toBe(401);

    const res2 = fakeRes();
    resp.sendForbidden(res2);
    expect(res2._status).toBe(403);
  });
});
