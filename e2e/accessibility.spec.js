import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const routes = ['/', '/login', '/register', '/pricing', '/templates', '/privacy', '/terms', '/refund', '/forgot-password'];

// /templates renders 60 animated template cards; axe's computed-style pass over
// that DOM takes longer than the 30s default and times out before it can report.
test.setTimeout(90_000);

/**
 * Framer-motion reveal animations are JS-driven (inline opacity), so the CSS
 * prefers-reduced-motion block does not stop them. Scanning mid-fade blends
 * text into the background and reports false WCAG contrast failures that vary
 * run to run. Settle on the final painted state before scanning.
 */
async function settle(page) {
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(900);
}

for (const route of routes) {
  test(`accessibility: ${route}`, async ({ page }) => {
    await page.goto(route);
    await settle(page);
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });
}
