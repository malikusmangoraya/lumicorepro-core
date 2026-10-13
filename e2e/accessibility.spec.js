import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const routes = ['/', '/login', '/register', '/pricing', '/templates', '/privacy', '/terms', '/refund', '/forgot-password'];

for (const route of routes) {
  test(`accessibility: ${route}`, async ({ page }) => {
    await page.goto(route);
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });
}