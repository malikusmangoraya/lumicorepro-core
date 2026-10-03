import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * captchaVerify reads its configuration from process.env at module load time, so
 * each scenario needs a fresh module instance. `loadModule` sets the env first
 * and then imports the module, which is the only way to exercise both the
 * "secret configured" and "no secret" code paths.
 */
async function loadModule(env) {
  const saved = { ...process.env };
  Object.assign(process.env, env);
  jest.resetModules();
  const mod = await import('../../middleware/captchaVerify.js');
  const restore = () => {
    for (const key of Object.keys(process.env)) {
      if (!(key in saved)) delete process.env[key];
    }
    Object.assign(process.env, saved);
  };
  return { mod, restore };
}

const fakeRes = () => {
  const res = {};
  res.status = jest.fn((c) => {
    res._status = c;
    return res;
  });
  res.json = jest.fn((b) => {
    res._body = b;
    return res;
  });
  return res;
};

const originalFetch = global.fetch;

afterEach(() => {
  global.fetch = originalFetch;
  delete process.env.TURNSTILE_SECRET_KEY;
  delete process.env.TURNSTILE_ENABLED;
});

describe('captchaVerify - requireCaptcha with no secret configured', () => {
  let mod;
  beforeEach(async () => {
    const loaded = await loadModule({
      TURNSTILE_ENABLED: 'true',
      TURNSTILE_SECRET_KEY: '',
      NODE_ENV: 'test',
    });
    mod = loaded.mod;
  });

  it('passes straight through (dev DX is not blocked)', () => {
    const next = jest.fn();
    const res = fakeRes();
    mod.requireCaptcha({ body: {} }, res, next);
    expect(next).toHaveBeenCalledTimes(1);
    expect(res.status).not.toHaveBeenCalled();
  });
});

describe('captchaVerify - requireCaptcha with a secret configured', () => {
  let mod;
  beforeEach(async () => {
    const loaded = await loadModule({
      TURNSTILE_ENABLED: 'true',
      TURNSTILE_SECRET_KEY: 'test-secret-value',
      NODE_ENV: 'test',
    });
    mod = loaded.mod;
  });

  it('rejects a missing token with 400 CAPTCHA_REQUIRED', () => {
    const next = jest.fn();
    const res = fakeRes();
    mod.requireCaptcha({ body: {} }, res, next);
    expect(res._status).toBe(400);
    expect(res._body.error.code).toBe('CAPTCHA_REQUIRED');
    expect(next).not.toHaveBeenCalled();
  });

  it('rejects a too-short token without calling Cloudflare', async () => {
    global.fetch = jest.fn();
    const res = fakeRes();
    mod.requireCaptcha({ body: { captchaToken: 'short' } }, res, jest.fn());
    expect(res._status).toBe(400);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('rejects a non-string token', () => {
    const res = fakeRes();
    mod.requireCaptcha({ body: { captchaToken: 1234567890123 } }, res, jest.fn());
    expect(res._status).toBe(400);
  });

  it.each([
    ['body.captchaToken', { body: { captchaToken: 'a'.repeat(20) } }],
    ['body.cf_turnstile_response', { body: { cf_turnstile_response: 'b'.repeat(20) } }],
    ['x-captcha-token header', { body: {}, headers: { 'x-captcha-token': 'c'.repeat(20) } }],
  ])('accepts the token from %s when verification succeeds', async (_label, req) => {
    global.fetch = jest.fn(async () => ({
      json: async () => ({ success: true }),
    }));
    const next = jest.fn();
    mod.requireCaptcha(req, fakeRes(), next);
    await new Promise((r) => setImmediate(r));
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('sends the secret and response to the siteverify endpoint', async () => {
    global.fetch = jest.fn(async () => ({ json: async () => ({ success: true }) }));
    mod.requireCaptcha(
      { body: { captchaToken: 'd'.repeat(20) }, ip: '203.0.113.9' },
      fakeRes(),
      jest.fn()
    );
    await new Promise((r) => setImmediate(r));

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://challenges.cloudflare.com/turnstile/v0/siteverify');
    expect(init.method).toBe('POST');
    expect(init.body.get('secret')).toBe('test-secret-value');
    expect(init.body.get('response')).toBe('d'.repeat(20));
    expect(init.body.get('remoteip')).toBe('203.0.113.9');
  });

  it('omits remoteip when the request has no IP', async () => {
    global.fetch = jest.fn(async () => ({ json: async () => ({ success: true }) }));
    mod.requireCaptcha(
      { body: { captchaToken: 'e'.repeat(20) } },
      fakeRes(),
      jest.fn()
    );
    await new Promise((r) => setImmediate(r));
    expect(global.fetch.mock.calls[0][1].body.has('remoteip')).toBe(false);
  });

  it('returns 403 CAPTCHA_FAILED when Cloudflare rejects the token', async () => {
    global.fetch = jest.fn(async () => ({
      json: async () => ({ success: false, 'error-codes': ['invalid-input-response'] }),
    }));
    const next = jest.fn();
    const res = fakeRes();
    mod.requireCaptcha({ body: { captchaToken: 'f'.repeat(20) } }, res, next);
    await new Promise((r) => setImmediate(r));
    expect(res._status).toBe(403);
    expect(res._body.error.code).toBe('CAPTCHA_FAILED');
    expect(next).not.toHaveBeenCalled();
  });

  it('fails OPEN outside production when the verifier is unreachable', async () => {
    // verifyTurnstileToken deliberately fails open when NODE_ENV != production
    // so a local network blip does not block development.
    global.fetch = jest.fn(async () => {
      throw new Error('network down');
    });
    const next = jest.fn();
    mod.requireCaptcha({ body: { captchaToken: 'g'.repeat(20) } }, fakeRes(), next);
    await new Promise((r) => setImmediate(r));
    expect(next).toHaveBeenCalledTimes(1);
  });
});

describe('captchaVerify - fail-closed in production', () => {
  let mod;
  beforeEach(async () => {
    const loaded = await loadModule({
      TURNSTILE_ENABLED: 'true',
      TURNSTILE_SECRET_KEY: 'test-secret-value',
      NODE_ENV: 'production',
    });
    mod = loaded.mod;
  });

  it('returns 503 CAPTCHA_UNAVAILABLE when the verifier is unreachable', async () => {
    global.fetch = jest.fn(async () => {
      throw new Error('network down');
    });
    const next = jest.fn();
    const res = fakeRes();
    mod.requireCaptcha({ body: { captchaToken: 'g'.repeat(20) } }, res, next);
    await new Promise((r) => setImmediate(r));
    // an upstream network blip must not become a free pass for bots
    expect(res._status).toBe(503);
    expect(res._body.error.code).toBe('CAPTCHA_UNAVAILABLE');
    expect(next).not.toHaveBeenCalled();
  });

  it('still blocks a missing token in production', () => {
    const next = jest.fn();
    const res = fakeRes();
    mod.requireCaptcha({ body: {} }, res, next);
    expect(res._status).toBe(400);
    expect(next).not.toHaveBeenCalled();
  });
});

describe('captchaVerify - optionalCaptcha', () => {
  it('marks verified=true and continues when no token is present', async () => {
    const loaded = await loadModule({
      TURNSTILE_ENABLED: 'true',
      TURNSTILE_SECRET_KEY: 'test-secret-value',
      NODE_ENV: 'test',
    });
    const req = { body: {} };
    const next = jest.fn();
    loaded.mod.optionalCaptcha(req, fakeRes(), next);
    expect(req.captchaVerified).toBe(false);
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('never blocks: continues even when verification fails', async () => {
    const loaded = await loadModule({
      TURNSTILE_ENABLED: 'true',
      TURNSTILE_SECRET_KEY: 'test-secret-value',
      NODE_ENV: 'test',
    });
    global.fetch = jest.fn(async () => ({ json: async () => ({ success: false }) }));
    const req = { body: { captchaToken: 'h'.repeat(20) } };
    const next = jest.fn();
    loaded.mod.optionalCaptcha(req, fakeRes(), next);
    await new Promise((r) => setImmediate(r));
    expect(req.captchaVerified).toBe(false);
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('marks verified=true on success', async () => {
    const loaded = await loadModule({
      TURNSTILE_ENABLED: 'true',
      TURNSTILE_SECRET_KEY: 'test-secret-value',
      NODE_ENV: 'test',
    });
    global.fetch = jest.fn(async () => ({ json: async () => ({ success: true }) }));
    const req = { body: { captchaToken: 'i'.repeat(20) } };
    const next = jest.fn();
    loaded.mod.optionalCaptcha(req, fakeRes(), next);
    await new Promise((r) => setImmediate(r));
    expect(req.captchaVerified).toBe(true);
    expect(next).toHaveBeenCalledTimes(1);
  });
});

describe('captchaVerify - disabled via env', () => {
  it('is a no-op when TURNSTILE_ENABLED=false', () => {
    const loaded = loadModule({
      TURNSTILE_ENABLED: 'false',
      TURNSTILE_SECRET_KEY: 'test-secret-value',
      NODE_ENV: 'test',
    });
    return loaded.then(({ mod }) => {
      const next = jest.fn();
      mod.requireCaptcha({ body: {} }, fakeRes(), next);
      expect(next).toHaveBeenCalledTimes(1);
    });
  });
});
