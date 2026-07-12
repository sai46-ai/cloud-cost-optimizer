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

  test('Admin Platform Walkthrough and Page Verification', async ({ page }) => {
    test.setTimeout(60000);
    // 1. Login using the standard input flow
    await page.goto('/login');
    const emailField = page.locator('input[type="email"]');
    const passwordField = page.locator('input[type="password"]');
    
    await emailField.click();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await emailField.fill('admin@gmail.com');
    
    await passwordField.click();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await passwordField.fill('123456789');
    
    await page.locator('button[type="submit"]').click();
    
    // 2. Wait for dashboard redirection
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    
    // 3. Walk through each page in the application to ensure it loads cleanly
    const pages = [
      '/dashboard',
      '/analytics',
      '/resources',
      '/ai-insights',
      '/budgets',
      '/reports',
      '/admin/dashboard',
      '/admin/users',
      '/admin/audit-logs',
      '/settings',
      '/profile'
    ];
    
    for (const p of pages) {
      await page.goto(p);
      await page.waitForLoadState('domcontentloaded');
      await page.locator('main').waitFor({ state: 'visible', timeout: 8000 });
      // Ensure the page doesn't show connection failures or offline mode toasts
      const offlineBanner = page.locator('text="Connecting to server... You are currently in offline mode."');
      await expect(offlineBanner).not.toBeVisible();
    }
  });

  test('Settings Audit Trail Visibility Guard for Normal Users', async ({ page }) => {
    // 1. Login as standard user
    await page.goto('/login');
    const emailField = page.locator('input[type="email"]');
    const passwordField = page.locator('input[type="password"]');
    
    await emailField.click();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await emailField.fill('testuser3@test.com');
    
    await passwordField.click();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await passwordField.fill('password123');
    
    await page.locator('button[type="submit"]').click();
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    
    // 2. Go to settings and check that Audit Trail tab is NOT visible
    await page.goto('/settings');
    await page.waitForLoadState('domcontentloaded');
    await page.locator('main').waitFor({ state: 'visible' });
    
    const auditTabBtn = page.locator('button:has-text("Audit Trail")');
    await expect(auditTabBtn).not.toBeVisible();
    
    // 3. Attempt direct access via query param
    await page.goto('/settings?tab=audit');
    await page.waitForLoadState('domcontentloaded');
    
    // Should fallback to general tab
    await page.waitForURL('**/settings?tab=general');
    const auditHeader = page.locator('text="Governance & Audit Trail"');
    await expect(auditHeader).not.toBeVisible();
  });
});
