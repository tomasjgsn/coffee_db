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
	await expect(page.getByText(/Ideal-zone hit rate/)).toBeVisible();
	const dots = await page.locator('.chart-frame circle.dot').count();
	expect(dots).toBeGreaterThan(30);
});

test('picking a bean draws its dial-in journey and refits the panels', async ({ page }) => {
	await page.goto('/chart');
	const before = await page.locator('.chart-frame circle.dot').count();
	await page.getByLabel('Filter by bean').selectOption('Raro Boda');
	await expect(page.getByText(/each dotted step is the next brew/)).toBeVisible();
	await expect.poll(async () => page.locator('.chart-frame circle.dot').count()).toBeLessThan(before);
});

test('hovering a dot shows the mini-label card', async ({ page }) => {
	await page.goto('/chart');
	await page.locator('.chart-frame circle.dot').last().hover();
	const card = page.getByRole('tooltip');
	await expect(card).toBeVisible();
	await expect(card.locator('.bean')).not.toBeEmpty();
	await expect(card.locator('.vitals')).toContainText('·');
});

test('clicking a dot pins the card with a link to the cup', async ({ page }) => {
	await page.goto('/chart');
	const dot = page.locator('.chart-frame circle.dot').last();
	await dot.hover();
	await dot.click();
	const card = page.getByRole('tooltip');
	await expect(card.getByText('Open this cup →')).toBeVisible();
	await card.getByText('Open this cup →').click();
	await page.waitForURL(/\/log\/\d+/);
	await expect(page.getByText(/Cup Nº \d+/)).toBeVisible();
});

test('tinting by grind shows the ramp legend', async ({ page }) => {
	await page.goto('/chart');
	await expect(page.getByTestId('tint-legend')).toHaveCount(0);
	await page.getByLabel('Tint dots by').selectOption('grind');
	await expect(page.getByTestId('tint-legend')).toBeVisible();
	await expect(page.getByTestId('tint-legend')).toContainText('pale → dark');
});

test('the method filter narrows the dots and the stats follow', async ({ page }) => {
	await page.goto('/chart');
	const before = await page.locator('.chart-frame circle.dot').count();
	await page.getByLabel('Filter by method').selectOption('hario-switch');
	await expect.poll(async () => page.locator('.chart-frame circle.dot').count()).toBeLessThan(before);
	await expect(page.getByText(/\d+ of \d+ measured cups/)).toBeVisible();
});

test('the learning strip renders all four variable panels', async ({ page }) => {
	await page.goto('/chart');
	await expect(page.getByText(/What moves the needle/)).toBeVisible();
	for (const title of ['Grind', 'Temp (°C)', 'Ratio (:1)', 'Rest (days)']) {
		await expect(page.locator('.panels').getByText(title, { exact: true })).toBeVisible();
	}
	await expect(page.getByText('By flavor profile')).toBeVisible();
});
