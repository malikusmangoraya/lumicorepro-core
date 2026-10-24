import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const sentry = vi.hoisted(() => ({
  init: vi.fn(),
  captureException: vi.fn((error) => `event-${error.message}`),
  setUser: vi.fn(),
  setTag: vi.fn(),
}));

vi.mock('@sentry/react', () => sentry);

const DSN = 'https://public@o0.ingest.sentry.io/42';

async function loadSentry(dsnValue) {
  vi.resetModules();
  vi.stubEnv('VITE_SENTRY_DSN', dsnValue ?? '');
  return import('../../utils/sentry');
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe('sentry without a DSN', () => {
  it('never loads the SDK and resolves every helper to a no-op', async () => {
    const mod = await loadSentry(undefined);

    await expect(mod.initSentry()).resolves.toBe(false);
    await expect(mod.captureError(new Error('boom'))).resolves.toBeNull();
    await expect(mod.setSentryUser({ id: 7, email: 'a@b.test' })).resolves.toBeUndefined();
    await expect(mod.setTraceId('trace-1')).resolves.toBeUndefined();

    expect(sentry.init).not.toHaveBeenCalled();
    expect(sentry.captureException).not.toHaveBeenCalled();
    expect(sentry.setUser).not.toHaveBeenCalled();
    expect(sentry.setTag).not.toHaveBeenCalled();
  });
});

describe('sentry with a DSN', () => {
  it('initialises once with tracing options and redacts credentials in beforeSend', async () => {
    const mod = await loadSentry(DSN);

    await expect(mod.initSentry()).resolves.toBe(true);
    expect(sentry.init).toHaveBeenCalledTimes(1);

    const options = sentry.init.mock.calls[0][0];
    expect(options).toMatchObject({
      dsn: DSN,
      tracesSampleRate: 0.1,
      replaysSessionSampleRate: 0,
      replaysOnErrorSampleRate: 0.2,
    });
    expect(options.release).toMatch(/^lumicorepro@/);

    const event = options.beforeSend({
      request: { url: 'https://app.test/page?api_key=secret&token=abc&keep=1' },
    });
    expect(event.request.url).toBe(
      'https://app.test/page?api_key=[redacted]&token=[redacted]&keep=1'
    );

    // A second call is a no-op — init must not run twice.
    await expect(mod.initSentry()).resolves.toBe(true);
    expect(sentry.init).toHaveBeenCalledTimes(1);
  });

  it('captures errors, sets the user, and tags the scope with the trace id', async () => {
    const mod = await loadSentry(DSN);
    await mod.initSentry();

    await expect(mod.captureError(new Error('kaboom'), { route: '/checkout' })).resolves.toBe(
      'event-kaboom'
    );
    expect(sentry.captureException).toHaveBeenCalledWith(expect.any(Error), {
      extra: { route: '/checkout' },
    });

    await mod.setSentryUser({ id: 99, email: 'user@test.dev' });
    expect(sentry.setUser).toHaveBeenCalledWith({ id: '99', email: 'user@test.dev' });

    await mod.setSentryUser(null);
    expect(sentry.setUser).toHaveBeenLastCalledWith(null);

    await mod.setTraceId(12345);
    expect(sentry.setTag).toHaveBeenCalledWith('trace_id', '12345');
  });

  it('does not capture or tag before init has completed', async () => {
    const mod = await loadSentry(DSN);

    await expect(mod.captureError(new Error('early'))).resolves.toBeNull();
    await mod.setTraceId('trace-early');

    expect(sentry.captureException).not.toHaveBeenCalled();
    expect(sentry.setTag).not.toHaveBeenCalled();
  });
});
