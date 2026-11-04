import { describe, expect, it } from 'vitest';
import { createAuthConfig } from './authConfig.js';

describe('createAuthConfig', () => {
  it('reports missing provider settings instead of enabling a fake sign-in', () => {
    expect(createAuthConfig('', '')).toEqual({
      configured: false,
      reason: 'missing',
    });
  });

  it('rejects non-HTTPS provider URLs outside localhost', () => {
    expect(createAuthConfig('http://auth.example.com', 'public-anon-key')).toEqual({
      configured: false,
      reason: 'invalid-url',
    });
  });

  it('rejects server-only Supabase keys before they enter the browser bundle', () => {
    expect(createAuthConfig('https://project.supabase.co', 'sb_secret_do_not_use')).toEqual({
      configured: false,
      reason: 'invalid-key',
    });
    expect(
      createAuthConfig(
        'https://project.supabase.co',
        'header.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.signature'
      )
    ).toEqual({
      configured: false,
      reason: 'invalid-key',
    });
  });

  it('accepts a secure provider URL and its public anonymous key', () => {
    expect(createAuthConfig('https://project.supabase.co/', 'public-anon-key')).toEqual({
      configured: true,
      url: 'https://project.supabase.co',
      anonKey: 'public-anon-key',
    });
  });
});
