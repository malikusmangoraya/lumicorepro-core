import { describe, it, expect } from 'vitest';
import { loginRedirectFor } from '../../components/auth/RequireAuth';

/**
 * Open-redirect guard: /login?next= must only ever carry a same-origin path.
 * A payload like `//evil.com` or `https://evil.com` would otherwise bounce a
 * user (post-login) to an attacker-controlled site.
 */
describe('loginRedirectFor', () => {
  it('keeps a normal path', () => {
    expect(loginRedirectFor({ pathname: '/workspace', search: '' })).toBe(
      '/login?next=%2Fworkspace'
    );
  });

  it('keeps path + query string', () => {
    expect(loginRedirectFor({ pathname: '/generate', search: '?plan=pro' })).toBe(
      '/login?next=%2Fgenerate%3Fplan%3Dpro'
    );
  });

  it('neutralises protocol-relative payloads', () => {
    const out = loginRedirectFor({ pathname: '//evil.com', search: '' });
    expect(out).toBe('/login?next=%2F');
  });

  it('falls back to / for absolute URLs', () => {
    expect(loginRedirectFor({ pathname: 'https://evil.com', search: '' })).toBe(
      '/login?next=%2F'
    );
  });

  it('defaults to / when location is missing', () => {
    expect(loginRedirectFor(undefined)).toBe('/login?next=%2F');
  });
});
