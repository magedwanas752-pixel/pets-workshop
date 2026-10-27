import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const flaskPort = 5100;
const astroDevPort = 4321;

export default defineConfig({
  testDir: './e2e-tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: `http://localhost:${astroDevPort}`,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: `node start-test-server.js`,
      url: `http://localhost:${flaskPort}/api/auth/status`,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: `npx cross-env API_SERVER_URL=http://127.0.0.1:${flaskPort} npm run dev -- --no-clearScreen`,
      url: `http://localhost:${astroDevPort}`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
