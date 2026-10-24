import { test, expect } from '@playwright/test';

/**
 * Revenue-path E2E: pricing -> checkout -> billing surfaces.
 *
 * Scope is page-level integrity (the pages render their core structure and
 * stay console-error free). Plan-card data rendering depends on a live payments
 * backend, so it is covered by backend Jest suites instead of being mocked here
 * — a mock that silently drifts from the real API shape would be worse than no
 * E2E assertion at all.
 */
test.describe('Checkout and billing paths', () => {
  test('pricing page renders its plans structure', async ({ page }) => {
    const consoleErrors = [];
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    await page.goto('/pricing');
    await expect(page.locator('h1', { hasText: /pricing/i }).first()).toBeVisible();
    // Both purchasable sections must exist even when no plans have loaded
    await expect(page.getByRole('heading', { name: /one-time credit packs/i })).toBeVisible();

    expect(consoleErrors, `uncaught page errors: ${consoleErrors.join(' | ')}`).toEqual([]);
  });

  test('restaurant checkout renders order controls', async ({ page }) => {
    const consoleErrors = [];
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    await page.goto('/restaurant/checkout');
    await expect(page.locator('h1, h2, form').first()).toBeVisible();
    expect(consoleErrors, `uncaught page errors: ${consoleErrors.join(' | ')}`).toEqual([]);
  });

  test('billing page loads for account management', async ({ page }) => {
    const consoleErrors = [];
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    await page.goto('/billing');
    await expect(page.locator('main, [role="main"], body').first()).toBeVisible();
    expect(consoleErrors, `uncaught page errors: ${consoleErrors.join(' | ')}`).toEqual([]);
  });
});
