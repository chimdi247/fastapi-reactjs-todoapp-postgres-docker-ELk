import { test, expect } from '@playwright/test';

test.describe('browser observability', () => {
  test('API calls carry a W3C traceparent header and spans are exported to the collector', async ({ page }) => {
    const apiTraceparents: string[] = [];
    page.on('request', (r) => {
      if (r.url().includes('/api/todos')) apiTraceparents.push(r.headers()['traceparent'] ?? '');
    });
    const exported = page.waitForRequest((r) => r.url().includes('/otlp/v1/traces') && r.method() === 'POST', { timeout: 15_000 });

    await page.goto('/todos');
    await expect(page.getByRole('heading', { name: /Todo/ })).toBeVisible();

    expect(apiTraceparents.length).toBeGreaterThan(0);
    expect(apiTraceparents[0]).toMatch(/^00-[0-9a-f]{32}-[0-9a-f]{16}-0[01]$/);
    await exported;
  });
});
