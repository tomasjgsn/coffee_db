import { expect, test } from '@playwright/test';

test('today shows the kettle CTA and pour-again shortcuts', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByRole('heading', { name: 'Today', exact: true })).toBeVisible();
	await expect(page.getByRole('link', { name: 'Start brew' })).toBeVisible();
	await expect(page.getByText('Brew again')).toBeVisible();
	await expect(page.getByText('Medals')).toBeVisible();
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
	await expect(page.getByText(/dial-in path: successive brews/)).toBeVisible();
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
	await expect(card.getByText('Open cup')).toBeVisible();
	await card.getByText('Open cup').click();
	await page.waitForURL(/\/log\/\d+/);
	await expect(page.getByText(/Cup \d+/)).toBeVisible();
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

test('iso-ratio guide rays are drawn and labeled on the chart', async ({ page }) => {
	await page.goto('/chart');
	await expect(page.locator('.chart-frame svg').getByText('1:16')).toBeVisible();
	await expect(page.locator('.chart-frame svg').getByText('1:18')).toBeVisible();
	await expect(page.getByText(/measured retention/)).toBeVisible();
});

test('filtering to the Switch raises the reachability advisory', async ({ page }) => {
	await page.goto('/chart');
	await expect(page.getByTestId('ray-advisory')).toHaveCount(0);
	await page.getByLabel('Filter by method').selectOption('hario-switch');
	await expect(page.getByTestId('ray-advisory')).toBeVisible();
	await expect(page.getByTestId('ray-advisory')).toContainText('above the ideal box');
	await expect(page.getByTestId('ray-advisory')).toContainText('Reachable between');
});

test('hovering a Switch cup shows the immersion reading', async ({ page }) => {
	await page.goto('/chart');
	await page.getByLabel('Filter by method').selectOption('hario-switch');
	await page.locator('.chart-frame circle.dot').last().hover();
	const card = page.getByRole('tooltip');
	await expect(card).toBeVisible();
	await expect(card.getByText(/immersion reading ≈/)).toBeVisible();
});

test('a too-tight plan ratio warns before brewing', async ({ page }) => {
	await page.goto('/brew');
	// Force a ratio the box can't be reached from: heavy dose, little water.
	await page.locator('input[name="doseG"]').fill('20');
	await page.locator('input[name="waterG"]').fill('240');
	await expect(page.getByTestId('plan-ray-advisory')).toBeVisible();
	await expect(page.getByTestId('plan-ray-advisory')).toContainText(/misses the ideal box|passes below/);
	// A comfortable ratio clears the warning.
	await page.locator('input[name="waterG"]').fill('360');
	await expect(page.getByTestId('plan-ray-advisory')).toHaveCount(0);
});

test('the learning strip renders all four variable panels', async ({ page }) => {
	await page.goto('/chart');
	await expect(page.getByText(/What moves the needle/)).toBeVisible();
	for (const title of ['Grind', 'Temp (°C)', 'Ratio (:1)', 'Rest (days)']) {
		await expect(page.locator('.panels').getByText(title, { exact: true })).toBeVisible();
	}
	await expect(page.getByText('By flavor profile')).toBeVisible();
});
