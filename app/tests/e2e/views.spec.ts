import { expect, test } from '@playwright/test';

test('the log lists real brews grouped by month', async ({ page }) => {
	await page.goto('/log');
	await expect(page.getByRole('heading', { name: 'The log' })).toBeVisible();
	// The sandbox seeds 61 legacy cups; companion tests may add more.
	await expect(page.getByText(/\d+ of \d+ cups/)).toBeVisible();
	expect(await page.locator('li').count()).toBeGreaterThanOrEqual(61);
	await expect(page.locator('li').filter({ hasText: 'Raro Boda' }).first()).toBeVisible();
});

test('a log row opens the bag-label detail page', async ({ page }) => {
	await page.goto('/log');
	await page.locator('li a').filter({ hasText: 'Raro Boda' }).first().click();
	await expect(page.getByText(/Cup Nº \d+/)).toBeVisible();
	await expect(page.getByText('Extraction', { exact: true })).toBeVisible();
});

test('filtering the log by bean narrows the list', async ({ page }) => {
	await page.goto('/log');
	const before = await page.locator('li').count();
	await page.getByLabel('Filter by bean').selectOption('Raro Boda');
	await expect(page.locator('li').filter({ hasText: 'La Providencia' })).toHaveCount(0);
	await expect
		.poll(async () => page.locator('li').count())
		.toBeLessThan(before);
});

test('the shelf shows deduped bean bags with stats', async ({ page }) => {
	await page.goto('/shelf');
	await expect(page.getByRole('heading', { name: 'The shelf' })).toBeVisible();
	await expect(page.getByText('10 bags')).toBeVisible();
	await expect(page.getByText('Raro Boda')).toBeVisible();
});
