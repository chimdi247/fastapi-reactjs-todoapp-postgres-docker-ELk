import { test as setup, expect } from '@playwright/test';

setup('log in as the seeded admin and save the session', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.ADMIN_EMAIL ?? 'admin@example.com');
  await page.getByLabel('Password').fill(process.env.ADMIN_PASSWORD ?? 'password123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/todos/);
  await page.context().storageState({ path: '.auth/admin.json' });
});
