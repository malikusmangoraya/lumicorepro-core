import { describe, it, expect, jest } from '@jest/globals';
import { z } from 'zod';
import validateRequest from '../../middleware/validateRequest.js';

const schema = {
  body: z.object({
    email: z.string().email(),
    age: z.number().int().min(18),
  }),
};

const fakeReq = (body) => ({ body });
const fakeNext = () => {};
const capture = () => {
  const res = {};
  res.status = jest.fn((c) => { res._status = c; return res; });
  res.json = jest.fn((b) => { res._body = b; return res; });
  return res;
};

describe('validateRequest middleware', () => {
  it('passes through valid bodies', () => {
    const req = fakeReq({ email: 'a@b.com', age: 30 });
    const res = capture();
    const next = jest.fn(fakeNext);
    validateRequest(schema)(req, res, next);
    expect(next).toHaveBeenCalled();
    expect(res._status).toBeUndefined();
  });

  it('returns 422 with issue details on invalid body', () => {
    const req = fakeReq({ email: 'not-an-email', age: 10 });
    const res = capture();
    const next = jest.fn(fakeNext);
    validateRequest(schema)(req, res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res._status).toBe(422);
    // Canonical envelope: code + details live at the top level, data is null.
    expect(res._body.success).toBe(false);
    expect(res._body.status).toBe(422);
    expect(res._body.code).toBe('VALIDATION_ERROR');
    expect(res._body.data).toBeNull();
    expect(res._body.details.length).toBeGreaterThan(0);
  });
});