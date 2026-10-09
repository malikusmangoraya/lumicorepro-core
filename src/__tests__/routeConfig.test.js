import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { routeConfig } from '../routes/routeConfig';

// Vitest serves transformed modules, so import.meta.url is not a file:// URL
// here; the test runner's cwd is always the repo root (vite.config.js).
const routerSource = readFileSync(
  resolve(process.cwd(), 'src', 'routes', 'index.jsx'),
  'utf8'
);

describe('routeConfig ↔ router consistency', () => {
  it('declares no duplicate paths', () => {
    const paths = routeConfig.map((route) => route.path);
    expect(new Set(paths).size).toBe(paths.length);
  });

  it('uses only the three documented access levels', () => {
    for (const route of routeConfig) {
      expect(['public', 'auth', 'admin']).toContain(route.access);
    }
  });

  it('every configured path exists in the router source', () => {
    for (const route of routeConfig) {
      const needle =
        route.path === '/' ? /path:\s*'\/'/ : `path: '${route.path}'`;
      const found =
        typeof needle === 'string' ? routerSource.includes(needle) : needle.test(routerSource);
      expect(found, `route "${route.path}" is configured but missing from index.jsx`).toBe(true);
    }
  });

  it('smoke routes are public-only (they run without a backend)', () => {
    const smoke = routeConfig.filter((route) => route.smoke);
    expect(smoke.length).toBeGreaterThan(0);
    for (const route of smoke) {
      expect(route.access, `smoke route "${route.path}" must be public`).toBe('public');
      expect(
        route.path.includes(':'),
        `smoke route "${route.path}" must not require route params`
      ).toBe(false);
    }
  });
});
