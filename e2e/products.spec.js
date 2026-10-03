import { expect, test } from '@playwright/test';

test.describe('Product listing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/templates/ecommerce/ProductListing');
  });

  test('renders the product catalog', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Product Listing' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Nova UI Kit' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Pulse Dashboard' })).toBeVisible();
  });

  test('filters products by category and search', async ({ page }) => {
    await page.getByRole('button', { name: 'UI Kits' }).click();
    await expect(page.getByRole('heading', { name: 'Nova UI Kit' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Commerce Pack' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Pulse Dashboard' })).toHaveCount(0);

    await page.getByPlaceholder('Search products…').fill('Commerce');
    await expect(page.getByRole('heading', { name: 'Commerce Pack' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Nova UI Kit' })).toHaveCount(0);
  });
});
