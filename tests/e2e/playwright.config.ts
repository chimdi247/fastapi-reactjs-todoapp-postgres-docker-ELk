import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.FRONTEND_URL ?? 'http://localhost:8080';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL, trace: 'on-first-retry', screenshot: 'only-on-failure', video: 'retain-on-failure' },
  projects: [
    // logs in once through the real UI and stores the session for the other specs
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: '.auth/admin.json' }, dependencies: ['setup'], testIgnore: /auth\.spec\.ts/ },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], storageState: '.auth/admin.json' }, dependencies: ['setup'], testIgnore: /auth\.spec\.ts/ },
    // login/logout specs must start anonymous
    { name: 'anonymous', use: { ...devices['Desktop Chrome'] }, testMatch: /auth\.spec\.ts/ },
  ],
});
