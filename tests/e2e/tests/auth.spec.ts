import { test, expect } from '@playwright/test';

const EMAIL = process.env.ADMIN_EMAIL ?? 'admin@example.com';
const PASSWORD = process.env.ADMIN_PASSWORD ?? 'password123';

test.describe('authentication', () => {
  test('anonymous users are redirected to /login from protected pages', async ({ page }) => {
    for (const path of ['/todos', '/add', '/todos/1/edit']) {
      await page.goto(path);
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test('wrong password shows an error and stays on /login', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill(EMAIL);
    await page.getByLabel('Password').fill('not-the-password');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('alert')).toContainText('Invalid email or password');
    await expect(page).toHaveURL(/\/login/);
  });

  test('admin can sign in, is sent back to the page they wanted, and can log out', async ({ page }) => {
    await page.goto('/add');                                   // protected -> /login
    await page.getByLabel('Email').fill(EMAIL);
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL(/\/add/);                     // returned to original target
    await expect(page.getByTestId('nav-user')).toHaveText(EMAIL);

    await page.getByRole('button', { name: 'Log out' }).click();
    await expect(page).toHaveURL(/\/login/);
    await page.goto('/todos');
    await expect(page).toHaveURL(/\/login/);                   // session really gone
  });

  test('an expired/invalid token sends the user back to /login', async ({ page }) => {
    await page.goto('/login');
    await page.evaluate(() => localStorage.setItem('todo.session.v1', JSON.stringify({
      token: 'garbage', expiresAt: Date.now() + 3_600_000,
      user: { id: 1, email: 'admin@example.com', full_name: null, role: 'admin' } })));
    await page.goto('/todos');                                 // API answers 401 -> session cleared
    await expect(page).toHaveURL(/\/login/);
  });
});
