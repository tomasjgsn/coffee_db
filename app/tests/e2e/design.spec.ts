import { expect, test } from '@playwright/test';

test('masthead and nav render on the design system page', async ({ page }) => {
	await page.goto('/design');
	await expect(page.getByRole('heading', { name: /the\s*counter/i })).toBeVisible();
	await expect(page.getByRole('navigation', { name: 'Primary' })).toBeVisible();
	for (const label of ['Today', 'Brew', 'The log', 'The chart', 'The shelf']) {
		await expect(page.getByRole('link', { name: label, exact: true })).toBeVisible();
	}
});

test('design page shows the three voices and the brewer set', async ({ page }) => {
	await page.goto('/design');
	await expect(page.getByText('Hamararo').first()).toBeVisible();
	await expect(page.getByRole('img', { name: 'V60 brush drawing' }).first()).toBeVisible();
	await expect(page.getByRole('img', { name: 'Hario Switch brush drawing' })).toBeVisible();
	await expect(page.getByRole('img', { name: 'Aeropress brush drawing' })).toBeVisible();
	await expect(page.getByRole('img', { name: 'Chemex brush drawing' })).toBeVisible();
	await expect(page.getByRole('img', { name: /ideal zone stamp/i })).toBeVisible();
});

test('every nav destination responds', async ({ page }) => {
	for (const path of ['/', '/brew', '/log', '/chart', '/shelf']) {
		const response = await page.goto(path);
		expect(response?.status()).toBe(200);
	}
});
