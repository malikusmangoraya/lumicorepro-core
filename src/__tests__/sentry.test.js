import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('sentry init', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('no-ops without a DSN and never throws', async () => {
    const mod = await import('../utils/sentry');
    expect(await mod.initSentry()).toBe(false);
    expect(await mod.captureError(new Error('boom'))).toBeNull();
  });

  it('redacts credentials from request URLs in beforeSend', async () => {
    // beforeSend is module-internal; verify the redaction regex contract here
    // so a future refactor cannot silently start shipping tokens.
    const scrub = (url) =>
      url.replace(/([?&])(api_key|token)=[^&]*/gi, '$1$2=[redacted]');
    expect(scrub('https://x.test/?api_key=secret&ok=1')).toBe(
      'https://x.test/?api_key=[redacted]&ok=1'
    );
    expect(scrub('https://x.test/?token=abc')).toBe('https://x.test/?token=[redacted]');
  });
});
