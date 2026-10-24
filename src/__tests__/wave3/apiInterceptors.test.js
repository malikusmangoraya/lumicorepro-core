import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import api from '../../services/api';

const TRACEPARENT_RE = /^00-[0-9a-f]{32}-[0-9a-f]{16}-01$/;

const header = (config, name) =>
  typeof config.headers?.get === 'function' ? config.headers.get(name) : config.headers?.[name];

const okResponse = (config, data = { ok: true }, headers = {}) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers,
  config,
});

const httpError = (config, status, message = `Request failed with status code ${status}`) => {
  const error = new Error(message);
  error.config = config;
  error.response = { status, data: {}, headers: {} };
  error.isAxiosError = true;
  return error;
};

let adapter;

beforeEach(() => {
  localStorage.clear();
  window.history.replaceState({}, '', '/');
  adapter = vi.fn();
  api.defaults.adapter = adapter;
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('api request interceptor', () => {
  it('injects the auth token, org header, traceparent, and strips a duplicated /api prefix', async () => {
    localStorage.setItem('auth_token', 'jwt-123');
    localStorage.setItem('active_org_id', 'org-9');
    adapter.mockImplementation(async (config) => okResponse(config, {}, { 'x-trace-id': 'trace-abc' }));

    const response = await api.get('/api/products');

    expect(adapter).toHaveBeenCalledTimes(1);
    const config = adapter.mock.calls[0][0];
    expect(config.url).toBe('/products');
    expect(header(config, 'Authorization')).toBe('Bearer jwt-123');
    expect(header(config, 'x-org-id')).toBe('org-9');
    expect(header(config, 'traceparent')).toMatch(TRACEPARENT_RE);
    expect(response.traceId).toBe('trace-abc');
  });

  it('omits auth and org headers for anonymous requests and keeps a supplied traceparent', async () => {
    adapter.mockImplementation(async (config) => okResponse(config));

    await api.get('/products', { headers: { traceparent: '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01' } });

    const config = adapter.mock.calls[0][0];
    expect(header(config, 'Authorization')).toBeUndefined();
    expect(header(config, 'x-org-id')).toBeUndefined();
    expect(header(config, 'traceparent')).toBe(
      '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01'
    );
  });

  it('rejects with the original error when the adapter rejects', async () => {
    const failure = new Error('adapter exploded');
    adapter.mockRejectedValue(failure);

    await expect(api.get('/products')).rejects.toBe(failure);
  });
});

describe('api response interceptor — 401 handling', () => {
  it('refreshes once for concurrent 401s and retries both requests with the new token', async () => {
    localStorage.setItem('auth_token', 'old-token');
    let refreshCalls = 0;

    adapter.mockImplementation(async (config) => {
      if (config.url === '/auth/refresh') {
        refreshCalls += 1;
        return okResponse(config, { token: 'new-token' });
      }
      if (header(config, 'Authorization') === 'Bearer old-token') {
        throw httpError(config, 401);
      }
      return okResponse(config, { url: config.url });
    });

    const [first, second] = await Promise.all([api.get('/orders'), api.get('/cart')]);

    expect(refreshCalls).toBe(1);
    expect(localStorage.getItem('auth_token')).toBe('new-token');
    expect(header(first.config, 'Authorization')).toBe('Bearer new-token');
    expect(header(second.config, 'Authorization')).toBe('Bearer new-token');
    // 2 initial requests + 1 refresh + 2 retries
    expect(adapter).toHaveBeenCalledTimes(5);
  });

  it('does not try to refresh a failed login request', async () => {
    localStorage.setItem('auth_token', 'old-token');
    adapter.mockImplementation(async (config) => {
      throw httpError(config, 401, 'Invalid credentials');
    });

    await expect(api.post('/auth/login', { email: 'a@b.test' })).rejects.toThrow(
      'Invalid credentials'
    );

    // Only the login call — no /auth/refresh attempt.
    expect(adapter).toHaveBeenCalledTimes(1);
  });

  it('clears the token and rejects when the refresh call fails', async () => {
    localStorage.setItem('auth_token', 'old-token');
    window.history.replaceState({}, '', '/login');
    adapter.mockImplementation(async (config) => {
      if (config.url === '/auth/refresh') throw httpError(config, 500, 'refresh failed');
      throw httpError(config, 401, 'unauthenticated');
    });

    await expect(api.get('/orders')).rejects.toThrow('unauthenticated');

    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('does not retry twice: a 401 on an already-retried request is rejected as-is', async () => {
    localStorage.setItem('auth_token', 'old-token');
    let orderCalls = 0;
    adapter.mockImplementation(async (config) => {
      if (config.url === '/auth/refresh') return okResponse(config, { token: 'new-token' });
      orderCalls += 1;
      throw httpError(config, 401, orderCalls === 1 ? 'first' : 'still unauthorized');
    });

    await expect(api.get('/orders')).rejects.toThrow('still unauthorized');
    expect(orderCalls).toBe(2);
  });
});
