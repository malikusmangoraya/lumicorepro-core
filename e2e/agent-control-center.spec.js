import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Agent Control Center', () => {
  test('renders the protected route with a recoverable signed-out state', async ({ page }) => {
    await page.goto('/workspace');
    await expect(page).toHaveURL(/\/login/);
  });

  test('keeps the workspace tab strip operable at mobile width when authenticated', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'e2e-token');
      localStorage.setItem('auth', JSON.stringify({ user: { id: 'e2e-user' }, token: 'e2e-token' }));
      localStorage.setItem('lmc_last_run_id', 'e2e-run');
    });
    await page.route('**/*watchtower*', (route) => route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ success: false, message: 'Agent backend unavailable' }),
    }));
    await page.route('**/*notifications/webhooks*', (route) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: { webhooks: [] } }),
    }));

    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/workspace');
    await expect(page.getByRole('heading', { name: /agent control center/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Browser QA' })).toBeVisible();
    await expect(page.getByLabel('Project Run ID')).toHaveValue('e2e-run');
    await expect(page.getByText(/analytics unavailable/i).first()).toBeVisible({ timeout: 15000 });

    // JS-driven reveal animations blend opacity; scan only the settled state
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(900);
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((violation) => ['critical', 'serious'].includes(violation.impact))).toEqual([]);
  });
});
