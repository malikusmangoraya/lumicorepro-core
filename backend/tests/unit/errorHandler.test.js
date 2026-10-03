import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';

/**
 * Global 404 + error handler.
 *
 * The two production bugs this pins down:
 *   1. `notFound` used to call `res.json(resp.sendNotFound(...))` — the helper
 *      already wrote the response, so the response object was serialized a
 *      second time (double response / circular JSON).
 *   2. The handler must never leak `err.stack` (or a raw DB message) in
 *      production.
 */

const loggerError = jest.fn();
const silentLogger = {
  error: loggerError,
  warn: () => {},
  info: () => {},
  http: () => {},
  debug: () => {},
};

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: silentLogger,
  withRequestId: () => silentLogger,
  redact: (v) => v,
}));

const { default: errorHandler, notFound } = await import('../../middleware/errorHandler.js');
const { default: AppError } = await import('../../utils/errors.js');

const ERROR_KEYS = ['success', 'status', 'message', 'code', 'data', 'timestamp'];

const makeRes = () => {
  const res = { statusCode: 200, headersSent: false };
  res.status = jest.fn((code) => {
    res.statusCode = code;
    return res;
  });
  res.json = jest.fn((body) => {
    res.body = body;
    res.headersSent = true;
    return res;
  });
  return res;
};

const makeReq = (method = 'GET', originalUrl = '/api/nope') => ({ method, originalUrl, ip: '127.0.0.1' });

const sorted = (keys) => [...keys].sort();

let savedNodeEnv;

beforeEach(() => {
  savedNodeEnv = process.env.NODE_ENV;
});

afterEach(() => {
  if (savedNodeEnv === undefined) delete process.env.NODE_ENV;
  else process.env.NODE_ENV = savedNodeEnv;
});

describe('notFound (404)', () => {
  it('writes the canonical envelope exactly once', () => {
    const req = makeReq('GET', '/api/does-not-exist');
    const res = makeRes();
    const next = jest.fn();

    notFound(req, res, next);

    expect(res.json).toHaveBeenCalledTimes(1);
    expect(res.status).toHaveBeenCalledWith(404);
    expect(Object.keys(res.body).sort()).toEqual(sorted(ERROR_KEYS));
    expect(res.body).toMatchObject({
      success: false,
      status: 404,
      code: 'NOT_FOUND',
      data: null,
    });
    expect(res.body.message).toContain('GET');
    expect(res.body.message).toContain('/api/does-not-exist');
    expect(Number.isNaN(Date.parse(res.body.timestamp))).toBe(false);
    expect(next).not.toHaveBeenCalled();
  });

  it('delegates instead of writing a second response when headers were sent', () => {
    const res = makeRes();
    res.headersSent = true;
    const next = jest.fn();

    notFound(makeReq(), res, next);

    expect(res.json).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalledTimes(1);
  });
});

describe('errorHandler', () => {
  it('returns the AppError status, code and message in the canonical envelope', () => {
    const req = makeReq('GET', '/api/orders/9');
    const res = makeRes();
    const next = jest.fn();

    errorHandler(new AppError('Order not found', 404, 'ORDER_NOT_FOUND'), req, res, next);

    expect(res.statusCode).toBe(404);
    expect(Object.keys(res.body).sort()).toEqual(sorted(ERROR_KEYS));
    expect(res.body).toMatchObject({
      success: false,
      status: 404,
      code: 'ORDER_NOT_FOUND',
      message: 'Order not found',
      data: null,
    });
    expect(next).not.toHaveBeenCalled();
  });

  it('derives the code from the status when the AppError omits one', () => {
    const res = makeRes();
    errorHandler(new AppError('Unauthorized', 401), makeReq(), res, jest.fn());

    expect(res.statusCode).toBe(401);
    expect(res.body.code).toBe('UNAUTHORIZED');
  });

  it('returns 500 and does NOT leak err.stack or the internal message in production', () => {
    process.env.NODE_ENV = 'production';
    const res = makeRes();
    const err = new Error('connection string postgres://user:pw@db failed');
    err.stack = 'Error: connection string postgres://user:pw@db failed\n    at secret.js:1:1';

    errorHandler(err, makeReq('POST', '/api/orders'), res, jest.fn());

    expect(res.statusCode).toBe(500);
    expect(res.body).toMatchObject({
      success: false,
      status: 500,
      code: 'INTERNAL_ERROR',
      message: 'Internal Server Error',
      data: null,
    });
    expect(Object.prototype.hasOwnProperty.call(res.body, 'stack')).toBe(false);
    const serialized = JSON.stringify(res.body);
    expect(serialized).not.toContain('secret.js');
    expect(serialized).not.toContain('at secret');
    expect(serialized).not.toContain('postgres://user:pw@db');
    expect(loggerError).toHaveBeenCalled();
  });

  it('never serializes a stack trace outside production either', () => {
    process.env.NODE_ENV = 'development';
    const res = makeRes();
    const err = new Error('boom');
    err.stack = 'Error: boom\n    at internal.js:5:5';

    errorHandler(err, makeReq(), res, jest.fn());

    expect(res.statusCode).toBe(500);
    expect(Object.prototype.hasOwnProperty.call(res.body, 'stack')).toBe(false);
    expect(JSON.stringify(res.body)).not.toContain('internal.js');
  });

  it('delegates to Express instead of double-writing when headers were sent', () => {
    const res = makeRes();
    res.headersSent = true;
    const err = new Error('stream failed midway');
    const next = jest.fn();

    errorHandler(err, makeReq(), res, next);

    expect(res.json).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalledWith(err);
  });

  it('serializes Sequelize validation errors as a canonical 400 with details', () => {
    const res = makeRes();
    const err = new Error('Validation error');
    err.name = 'SequelizeValidationError';
    err.errors = [{ message: 'email must be unique' }];

    errorHandler(err, makeReq(), res, jest.fn());

    expect(res.statusCode).toBe(400);
    expect(res.body.code).toBe('VALIDATION_ERROR');
    expect(res.body.details).toEqual(['email must be unique']);
    expect(res.body.data).toBeNull();
  });
});
