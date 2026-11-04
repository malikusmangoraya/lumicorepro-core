import { expect, test } from '@playwright/test';

const email = `client-demo-${Date.now()}@example.com`;
const password = 'DemoPassword123!';

test('sign-up, generate a streamed demo article, and reopen it from history', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => { if (message.type() === 'error') pageErrors.push(message.text()); });
  page.on('requestfailed', (request) => pageErrors.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText}`));

  await page.goto('/generate/history');
  await expect(page).toHaveURL(/\/login\?next=/);
  await expect(page.getByLabel('Email')).toBeVisible();

  await page.goto('/register');
  await page.getByLabel('Name').fill('Client Demo Writer');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel(/Password/).fill(password);
  await page.getByRole('button', { name: 'Create Account' }).click();
  await expect(page).toHaveURL(/\/generate$/);
  await expect(page.getByTestId('sidebar-balance')).toHaveText('50');

  await page.getByTestId('gen-keyword').fill('Practical AI writing workflows');
  await page.getByTestId('gen-submit').click();
  await expect(page.getByTestId('gen-article')).toBeVisible({ timeout: 45000 });
  await expect(page.getByText(/demo mode/)).toBeVisible();
  await expect(page.getByTestId('sidebar-balance')).toHaveText('49');

  await page.getByRole('link', { name: 'History' }).click();
  await expect(page.getByText('Practical AI writing workflows')).toBeVisible();
  await page.getByRole('button', { name: /Open/ }).click();
  await expect(page).toHaveURL(/\/generate$/);
  await expect(page.getByTestId('gen-article')).toBeVisible();
  expect(pageErrors).toEqual([]);
});
