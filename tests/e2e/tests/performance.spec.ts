import { test, expect } from '@playwright/test';

// Front-end performance budgets (lab conditions: local docker). Tune for your hardware.
const BUDGET = { fcpMs: 2500, domContentLoadedMs: 2500, jsTransferKB: 600 };

test('home page meets basic performance budgets', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'Paint/transfer metrics are only reliable in Chromium');
  let jsBytes = 0;
  page.on('response', async (r) => {
    if (r.url().endsWith('.js')) jsBytes += Number(r.headers()['content-length'] ?? 0);
  });
  await page.goto('/', { waitUntil: 'load' });

  const m = await page.evaluate(() => {
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const fcp = performance.getEntriesByName('first-contentful-paint')[0];
    return { fcp: fcp?.startTime ?? 0, dcl: nav.domContentLoadedEventEnd };
  });
  expect(m.fcp, 'first contentful paint').toBeGreaterThan(0);
  expect(m.fcp).toBeLessThan(BUDGET.fcpMs);
  expect(m.dcl).toBeLessThan(BUDGET.domContentLoadedMs);
  expect(jsBytes / 1024, 'JS transfer size (KB, gzip)').toBeLessThan(BUDGET.jsTransferKB);
});
