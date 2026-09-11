import { describe, it, expect } from '@jest/globals';
import { redact } from '../../utils/logger.js';

describe('Logger sensitive-data redaction', () => {
  it('redacts password/secret/token fields at any depth', () => {
    const input = {
      email: 'a@b.com',
      password: 'hunter2',
      nested: { apiKey: 'sk_test_123', jwt: 'eyJ.abc.def' },
      arr: [{ token: 'secret-token' }, { ok: 1 }],
    };
    const out = redact(input);
    expect(out.email).toBe('a@b.com');
    expect(out.password).toBe('[REDACTED]');
    expect(out.nested.apiKey).toBe('[REDACTED]');
    expect(out.nested.jwt).toBe('[REDACTED]');
    expect(out.arr[0].token).toBe('[REDACTED]');
    expect(out.arr[1].ok).toBe(1);
  });

  it('redacts JWT-looking strings even in plain messages', () => {
    const jwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';
    const input = { webtoken: jwt };
    expect(redact(input).webtoken).toBe('[REDACTED]');
  });

  it('leaves innocuous values unchanged', () => {
    const out = redact({ title: 'Order #1', total: 99.99, meta: { page: 1 } });
    expect(out).toEqual({ title: 'Order #1', total: 99.99, meta: { page: 1 } });
  });
});