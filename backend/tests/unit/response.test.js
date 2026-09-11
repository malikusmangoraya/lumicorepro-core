import { describe, it, expect, jest } from '@jest/globals';
import resp from '../../utils/response.js';

// Minimal express res mock
const fakeRes = () => {
  const res = {};
  res.status = jest.fn((c) => { res._status = c; return res; });
  res.json = jest.fn((b) => { res._body = b; return res; });
  return res;
};

describe('Response wrapper (standardized shape)', () => {
  it('sendSuccess returns { success:true, data }', () => {
    const res = fakeRes();
    resp.sendSuccess(res, { id: 1 });
    expect(res._status).toBe(200);
    expect(res._body).toEqual({ success: true, data: { id: 1 } });
  });

  it('sendSuccess attaches meta when provided', () => {
    const res = fakeRes();
    resp.sendSuccess(res, [], { page: 1, total: 50 }, 200);
    expect(res._body.meta).toEqual({ page: 1, total: 50 });
  });

  it('sendError returns { success:false, error:{code,message} }', () => {
    const res = fakeRes();
    resp.sendError(res, 'VALIDATION_ERROR', 'Bad input', 422);
    expect(res._status).toBe(422);
    expect(res._body).toEqual({
      success: false,
      error: { code: 'VALIDATION_ERROR', message: 'Bad input' },
    });
  });

  it('sendNotFound uses NOT_FOUND code and 404', () => {
    const res = fakeRes();
    resp.sendNotFound(res, 'Order');
    expect(res._status).toBe(404);
    expect(res._body.error.code).toBe('NOT_FOUND');
    expect(res._body.error.message).toContain('Order');
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