import { expect, test } from '@playwright/test';

test('masthead and nav render on the design reference page', async ({ page }) => {
	await page.goto('/design');
	await expect(page.getByRole('heading', { name: /the counter/i })).toBeVisible();
	await expect(page.getByRole('navigation', { name: 'Primary' })).toBeVisible();
	for (const label of ['today', 'brew', 'log', 'chart', 'shelf']) {
		await expect(page.getByRole('link', { name: label, exact: true })).toBeVisible();
	}
});

test('design reference shows the fields, the law, and the artifacts', async ({ page }) => {
	await page.goto('/design');
	await expect(page.getByRole('heading', { name: 'Color: fields, not fills' })).toBeVisible();
	await expect(page.getByRole('heading', { name: 'Type: the law' })).toBeVisible();
	await expect(page.getByRole('button', { name: 'Start brew' })).toBeVisible();
	await expect(page.getByRole('img', { name: /caustic pool/i })).toBeVisible();
});

test('every nav destination responds', async ({ page }) => {
	for (const path of ['/', '/brew', '/log', '/chart', '/shelf']) {
		const response = await page.goto(path);
		expect(response?.status()).toBe(200);
	}
});
