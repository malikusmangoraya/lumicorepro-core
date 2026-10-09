import { test, expect } from '@playwright/test';
import { routeConfig } from '../src/routes/routeConfig.js';

/**
 * Public-route smoke pass driven by src/routes/routeConfig.js — the same file
 * the vitest consistency test checks against the router, so config and router
 * cannot drift apart silently.
 *
 * These routes must render fully WITHOUT a backend: the e2e server only
 * serves the static production build. A blank #root means a crash-on-render
 * regression (the "builds green, renders nothing" failure mode this repo has
 * hit before), so that is exactly what this asserts against.
 */
const smokeRoutes = routeConfig.filter((route) => route.smoke).map((route) => route.path);

for (const routePath of smokeRoutes) {
  test(`public route ${routePath} renders without a backend`, async ({ page }) => {
    const url = routePath === '/' ? '/' : `/${routePath}`;
    const response = await page.goto(url);

    expect(response, `no response for ${url}`).not.toBeNull();
    expect(response.status(), `unexpected status for ${url}`).toBe(200);

    await expect(page.locator('#root'), `empty app shell for ${url}`).not.toBeEmpty();
  });
}
