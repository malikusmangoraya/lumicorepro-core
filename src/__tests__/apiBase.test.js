import { describe, expect, it } from 'vitest';
import { resolveApiBaseUrl } from '../services/apiBase';

describe('resolveApiBaseUrl', () => {
  it('uses the Vite proxy when no API URL is configured', () => {
    expect(resolveApiBaseUrl(undefined, true)).toBe('/api');
  });

  it('preserves an explicitly configured API origin', () => {
    expect(resolveApiBaseUrl('https://api.example.com/', true)).toBe('https://api.example.com/api');
  });

  it('stays same-origin in production when no API URL is configured', () => {
    // Single-service deploys serve the API from the same host; falling back to
    // localhost would make the browser call the visitor's own machine.
    expect(resolveApiBaseUrl(undefined, false)).toBe('/api');
    expect(resolveApiBaseUrl('', false)).toBe('/api');
  });
});
