import { test, expect } from '@playwright/test';

test.describe('UI Navigation and Hydration', () => {
  test('Landing Page loads correctly', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // Ensure no client-side crash
    const root = page.locator('#root');
    await expect(root).not.toBeEmpty();
  });

  test('Auth routes routing works', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('form').first()).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('Protected routes redirect to login', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });

  test('Checking 404 fallback', async ({ page }) => {
    await page.goto('/some-unknown-route');
    await page.waitForURL('**/');
    expect(page.url()).not.toContain('/some-unknown-route');
  });
});
