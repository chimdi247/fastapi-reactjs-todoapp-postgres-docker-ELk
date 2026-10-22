import { test, expect, type Page } from '@playwright/test';

const unique = (p: string) => `${p}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
const item = (page: Page, title: string) => page.locator('li.todos-page__item', { has: page.getByRole('heading', { name: title }) });

async function createTodo(page: Page, title: string, description = 'e2e description') {
  await page.goto('/add');
  await page.getByLabel('Task Title *').fill(title);
  await page.getByLabel('Description').fill(description);
  await page.getByRole('button', { name: 'Create Todo' }).click();
  await expect(page).toHaveURL(/\/todos$/);
}

test.describe('todos (authenticated)', () => {
  test('create, edit, complete and delete a todo', async ({ page }) => {
    const title = unique('e2e');
    await createTodo(page, title);
    await expect(item(page, title)).toBeVisible();
    await expect(item(page, title)).toContainText('e2e description');

    await item(page, title).getByRole('link', { name: 'Edit' }).click();
    const renamed = `${title}-renamed`;
    await page.getByLabel('Task Title *').fill(renamed);
    await page.getByLabel('Mark as completed').check();
    await page.getByRole('button', { name: 'Save Changes' }).click();

    await expect(item(page, renamed)).toBeVisible();
    await expect(item(page, renamed)).toHaveClass(/todos-page__item--completed/);

    await item(page, renamed).getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Yes, Delete' }).click();
    await expect(item(page, renamed)).toHaveCount(0);
  });

  test('cancelling the delete dialog keeps the todo', async ({ page }) => {
    const title = unique('keep');
    await createTodo(page, title);
    await item(page, title).getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(item(page, title)).toBeVisible();
    // cleanup
    await item(page, title).getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Yes, Delete' }).click();
  });

  test('title is required', async ({ page }) => {
    await page.goto('/add');
    await page.getByRole('button', { name: 'Create Todo' }).click();
    await expect(page).toHaveURL(/\/add/);
    await expect(page.getByLabel('Task Title *')).toHaveJSProperty('validity.valueMissing', true);
  });

  test('todos persist across a full reload (stored in PostgreSQL)', async ({ page }) => {
    const title = unique('persist');
    await createTodo(page, title);
    await page.reload();
    await expect(item(page, title)).toBeVisible();
    await item(page, title).getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Yes, Delete' }).click();
  });

  test('unknown routes fall back to the home page', async ({ page }) => {
    await page.goto('/definitely/not/a/page');
    await expect(page).toHaveURL(/\/$/);
  });
});
