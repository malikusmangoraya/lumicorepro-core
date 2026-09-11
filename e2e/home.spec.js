import { test, expect } from '@playwright/test';

test.describe('LumiCorePro E2E Navigation & Pages', () => {
  test('should load home page successfully', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/LumiCorePro/i);
  });

  test('should navigate to templates catalog', async ({ page }) => {
    await page.goto('/templates');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('should navigate to login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
  });
});
