import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

const appDirectory = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  timeout: 30_000,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:4173/lumicorepro-core/orbitboard/',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173 --strictPort',
    cwd: appDirectory,
    url: 'http://127.0.0.1:4173/lumicorepro-core/orbitboard/',
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
