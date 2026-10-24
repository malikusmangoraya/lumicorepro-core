import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: `http://localhost:${process.env.E2E_PORT || '5173'}`,
    trace: 'on-first-retry',
    // Page-enter/transition animations blend colors mid-fade; axe scans taken
    // during them report false contrast violations (measured 3.58:1 on a token
    // that is 4.6:1 at rest). The app honours prefers-reduced-motion (globals.css),
    // so forcing it makes scans deterministic — and matches the a11y contract.
    reducedMotion: 'reduce',
  },
  // Serve the production build, not the Vite dev server. The dev-time
  // dependency optimizer and per-module transforms take 19-34s per cold
  // request on this machine, and the HMR client is load-blocking, so `page.goto`
  // aborted with ERR_ABORTED on any cold checkout. `vite build` + `vite preview`
  // is ~5s, has no optimizer/HMR client, and tests the artifact that ships.
  webServer: {
    command: 'node scripts/e2e-server.mjs',
    url: `http://localhost:${process.env.E2E_PORT || '5173'}`,
    reuseExistingServer: !process.env.CI,
    timeout: 300000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
