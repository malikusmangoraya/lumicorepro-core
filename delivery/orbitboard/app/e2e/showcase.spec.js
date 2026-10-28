import { expect, test } from '@playwright/test';

test('primary navigation opens the feature page', async ({ page }) => {
  await page.goto('./');
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    'href',
    'https://malikusmangoraya.github.io/lumicorepro-core/orbitboard/'
  );
  await page
    .getByRole('navigation', { name: 'Primary navigation' })
    .getByRole('link', { name: 'Features', exact: true })
    .click();

  await expect(page).toHaveURL(/\/services$/);
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    'href',
    'https://malikusmangoraya.github.io/lumicorepro-core/orbitboard/services'
  );
  await expect(page.getByRole('heading', { name: /Useful structure/i })).toBeVisible();
  await expect(page).toHaveTitle(/Features — Orbitboard/);
});

test('public routes render useful pages and unknown routes get a 404 state', async ({ page }) => {
  const publicPages = [
    ['services', /Useful structure/i, /Features — Orbitboard/],
    ['about', /Planning is a conversation/i, /About — Orbitboard/],
    ['pricing', /Choose a view/i, /Pricing — Orbitboard/],
    ['contact', /No inbox here/i, /Contact — Orbitboard/],
    ['privacy', /Privacy for this preview/i, /Privacy — Orbitboard/],
    ['terms', /Terms for this preview/i, /Terms — Orbitboard/],
  ];

  for (const [route, heading, title] of publicPages) {
    await page.goto(`./${route}`);
    await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible();
    await expect(page).toHaveTitle(title);
  }

  await page.goto('./not-a-route');
  await expect(page.getByRole('heading', { name: /We can’t find that page/i })).toBeVisible();
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
});

test('mobile menu closes with Escape and returns keyboard focus', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('./');

  for (const width of [320, 390, 768, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }

  await page.setViewportSize({ width: 390, height: 844 });
  const menuButton = page.getByRole('button', { name: 'Menu' });
  await menuButton.click();
  await expect(menuButton).toHaveAttribute('aria-expanded', 'true');
  await expect(page.getByRole('navigation', { name: 'Primary navigation' })).toBeVisible();
  await page.keyboard.press('Escape');

  await expect(menuButton).toHaveAttribute('aria-expanded', 'false');
  await expect(menuButton).toBeFocused();
});

test('roadmap horizon and team filters update the sample and reset it', async ({ page }) => {
  await page.goto('./');

  const horizon = page.getByRole('combobox', { name: 'Time horizon' });
  const items = page.locator('.roadmap-item');
  await expect(items).toHaveCount(6);

  await horizon.selectOption('Q4 2026');
  await expect(items).toHaveCount(3);
  await expect(page.getByRole('heading', { name: 'Research library' })).toHaveCount(0);

  await page.getByRole('button', { name: 'Platform', exact: true }).click();
  await expect(items).toHaveCount(2);
  await expect(page.getByRole('heading', { name: 'Shared roadmap views' })).toBeVisible();

  await page.getByRole('button', { name: 'Reset sample' }).click();
  await expect(horizon).toHaveValue('all');
  await expect(page.getByRole('button', { name: 'All teams' })).toHaveAttribute('aria-pressed', 'true');
  await expect(items).toHaveCount(6);
});

test('account pages explain provider setup when authentication is not configured', async ({ page }) => {
  const unavailablePages = [
    ['login', /Authentication is not configured/i],
    ['register', /Authentication is not configured/i],
  ];

  for (const [route, heading] of unavailablePages) {
    await page.goto(`./${route}`);
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
    await expect(page.locator('form')).toHaveCount(0);
    await expect(page.getByText(/VITE_SUPABASE_URL/i)).toBeVisible();
  }
});

test('admin and checkout routes never present fake success flows', async ({ page }) => {
  const unavailablePages = [
    ['admin', /Admin tools are unavailable/i],
    ['checkout', /Checkout is unavailable/i],
  ];

  for (const [route, heading] of unavailablePages) {
    await page.goto(`./${route}`);
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
    await expect(page.locator('form')).toHaveCount(0);
    await expect(page.getByRole('link', { name: /Return to product preview/i })).toBeVisible();
  }
});
