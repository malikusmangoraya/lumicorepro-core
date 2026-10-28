import { expect, test } from '@playwright/test';

const authTestsEnabled = process.env.ORBITBOARD_AUTH_TESTS === '1';

test('sign-in creates an authenticated session and logout clears it', async ({ page }) => {
  test.skip(!authTestsEnabled, 'Run with ORBITBOARD_AUTH_TESTS=1 and test provider settings.');

  await page.route('https://auth.test.local/auth/v1/token**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'test-access-token',
        token_type: 'bearer',
        expires_in: 3600,
        refresh_token: 'test-refresh-token',
        user: {
          id: 'user-123',
          aud: 'authenticated',
          role: 'authenticated',
          email: 'member@example.com',
          created_at: '2026-10-28T00:00:00.000Z',
          app_metadata: { provider: 'email', providers: ['email'] },
          user_metadata: {},
        },
      }),
    });
  });
  await page.route('https://auth.test.local/auth/v1/logout**', (route) =>
    route.fulfill({ status: 204, body: '' })
  );

  await page.goto('./login');
  for (const width of [320, 390, 768, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
  await page.setViewportSize({ width: 1280, height: 844 });
  await page.getByLabel('Email address').fill('member@example.com');
  await page.getByLabel('Password').fill('correct horse battery');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page).toHaveURL(/\/account$/);
  await expect(page.getByText('member@example.com')).toBeVisible();
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
});

test('sign-in failure uses a safe generic message', async ({ page }) => {
  test.skip(!authTestsEnabled, 'Run with ORBITBOARD_AUTH_TESTS=1 and test provider settings.');

  await page.route('https://auth.test.local/auth/v1/token**', (route) =>
    route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({ code: 'invalid_credentials', message: 'Invalid login credentials' }),
    })
  );

  await page.goto('./login');
  await page.getByLabel('Email address').fill('member@example.com');
  await page.getByLabel('Password').fill('wrong-password');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('alert')).toHaveText('We could not sign you in with those details.');
});

test('registration asks the user to verify their email before signing in', async ({ page }) => {
  test.skip(!authTestsEnabled, 'Run with ORBITBOARD_AUTH_TESTS=1 and test provider settings.');

  await page.route('https://auth.test.local/auth/v1/signup**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-456',
        aud: 'authenticated',
        role: 'authenticated',
        email: 'new@example.com',
        created_at: '2026-10-28T00:00:00.000Z',
        app_metadata: { provider: 'email', providers: ['email'] },
        user_metadata: { display_name: 'New Member' },
        identities: [{ id: 'identity-456', user_id: 'user-456', identity_data: { email: 'new@example.com' } }],
      }),
    });
  });

  await page.goto('./register');
  await page.getByLabel('Full name').fill('New Member');
  await page.getByLabel('Email address').fill('new@example.com');
  await page.getByLabel('Password').fill('a-long-test-password');
  await page.getByRole('button', { name: 'Create account' }).click();

  await expect(page.getByRole('status')).toContainText(/verify your account/i);
  await expect(page).toHaveURL(/\/register$/);
});

test('password recovery provides a non-enumerating confirmation', async ({ page }) => {
  test.skip(!authTestsEnabled, 'Run with ORBITBOARD_AUTH_TESTS=1 and test provider settings.');

  await page.route('https://auth.test.local/auth/v1/recover**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  );

  await page.goto('./login');
  await page.getByRole('button', { name: 'Forgot password?' }).click();
  await page.getByLabel('Email address').fill('member@example.com');
  await page.getByRole('button', { name: 'Send recovery link' }).click();

  await expect(page.getByRole('status')).toContainText(/if an account exists/i);
});
