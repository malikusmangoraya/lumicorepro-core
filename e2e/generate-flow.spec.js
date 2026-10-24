import { test, expect } from '@playwright/test';

/**
 * Generate flow — the core product journey.
 * /generate is a PUBLIC route (only /workspace is auth-guarded), so the
 * contract under test is the composer itself: prompt textarea renders, the
 * primary action is disabled until a prompt exists, and filling the prompt
 * unlocks it. No API call is made until submit, so no backend is needed.
 */
test.describe('Generate flow', () => {
  test('prompt composer renders and gates the generate action on input', async ({ page }) => {
    const consoleErrors = [];
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    await page.goto('/generate');

    const promptBox = page.getByPlaceholder(/Build a restaurant website|restaurant website/i).first();
    // Heavy lazy graph (composer + provider list); allow the route time to mount
    await expect(promptBox).toBeVisible({ timeout: 20000 });

    // Primary action starts disabled with an empty prompt
    const generateBtn = page.getByRole('button', { name: /generate website/i }).first();
    await expect(generateBtn).toBeVisible();
    await expect(generateBtn).toBeDisabled();

    // Filling the prompt unlocks it
    await promptBox.fill('A landing page for a coffee roastery with online ordering');
    await expect(generateBtn).toBeEnabled();

    expect(consoleErrors, `uncaught page errors: ${consoleErrors.join(' | ')}`).toEqual([]);
  });

  test('example prompts are available as one-click starters', async ({ page }) => {
    await page.goto('/generate');
    const example = page.getByRole('button', { name: /use example:/i }).first();
    await expect(example).toBeVisible({ timeout: 20000 });
    await example.click();

    const promptBox = page.getByPlaceholder(/Build a restaurant website|restaurant website/i).first();
    await expect(promptBox).not.toHaveValue('');
  });

  test('workspace route loads without crashing', async ({ page }) => {
    const consoleErrors = [];
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    await page.goto('/workspace');
    await expect(page.locator('main, [role="main"], body').first()).toBeVisible();
    expect(consoleErrors, `uncaught page errors: ${consoleErrors.join(' | ')}`).toEqual([]);
  });
});
