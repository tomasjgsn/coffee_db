import { expect, test } from '@playwright/test';

test('today shows the kettle CTA and pour-again shortcuts', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByRole('heading', { name: 'Today', exact: true })).toBeVisible();
	await expect(page.getByRole('link', { name: /Put the kettle on/ })).toBeVisible();
	await expect(page.getByText('Pour it again')).toBeVisible();
	await expect(page.getByText('The stamp collection')).toBeVisible();
});

test('a pour-again shortcut lands on a preselected plan', async ({ page }) => {
	await page.goto('/');
	const shortcut = page.locator('a.again').first();
	const beanName = await shortcut.locator('.name').innerText();
	await shortcut.click();
	await page.waitForURL(/\/brew\?bean=\d+&method=.+/);
	await expect(page.locator('.bag-card.selected')).toContainText(beanName);
});

test('the chart draws the control chart with an ideal zone and stats', async ({ page }) => {
	await page.goto('/chart');
	await expect(page.getByRole('img', { name: /Brewing control chart/ })).toBeVisible();
	await expect(page.getByText('Ideal-zone hit rate · last 10')).toBeVisible();
	const dots = await page.locator('svg circle').count();
	expect(dots).toBeGreaterThan(30);
});

test('picking a bean draws its dial-in journey', async ({ page }) => {
	await page.goto('/chart');
	await page.locator('select').selectOption('Raro Boda');
	await expect(page.getByText(/measured cups · Raro Boda/)).toBeVisible();
	await expect(page.getByText(/walking it into the box/)).toBeVisible();
});
