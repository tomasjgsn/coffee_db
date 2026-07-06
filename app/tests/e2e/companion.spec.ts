import { expect, test, type Page } from '@playwright/test';

/**
 * The full brew companion: Plan → Brew (live timer, keyboard events) →
 * Taste → stamped into the log. Runs against the e2e sandbox database.
 */

async function planAndStart(page: Page): Promise<string> {
	await page.goto('/brew');
	await expect(page.getByRole('heading', { name: 'The bag' })).toBeVisible();
	// First bag is preselected; the recipe card prefills from its last brew.
	await expect(page.locator('input[name="doseG"]')).not.toHaveValue('0');
	await page.getByRole('button', { name: 'Start brew' }).click();
	await page.waitForURL(/\/brew\/\d+\/live/);
	const match = /\/brew\/(\d+)\/live/.exec(page.url());
	return match![1];
}

test('plan, brew with the keyboard, taste, and stamp a complete cup', async ({ page }) => {
	const id = await planAndStart(page);

	// Space starts the clock and marks the bloom.
	await page.keyboard.press('Space');
	await expect(page.locator('.events li').filter({ hasText: 'Bloom' })).toBeVisible();

	// End the bloom pour and log what the scale said.
	await page.keyboard.press('Space');
	const waterInput = page.getByLabel('Water at this point, grams');
	await expect(waterInput).toBeVisible();
	await waterInput.fill('54');
	await page.keyboard.press('Enter');
	await expect(page.locator('.events li').filter({ hasText: '54 g' })).toBeVisible();

	// A swirl, a second pour, then call the drawdown.
	await page.keyboard.press('s');
	await expect(page.locator('.events li').filter({ hasText: 'Swirl' })).toBeVisible();
	await page.keyboard.press('Space');
	await page.keyboard.press('Space');
	await page.keyboard.press('Escape');
	await page.keyboard.press('d');
	await expect(page.locator('.events li').filter({ hasText: 'Drawdown done' })).toBeVisible();

	await page.getByRole('button', { name: 'Taste', exact: true }).click();
	await page.waitForURL(`/brew/${id}/taste`);

	// Weights → live extraction; three-factor dots; stamp it.
	await page.locator('input[name="mugWeightG"]').fill('300');
	await page.locator('input[name="finalCombinedWeightG"]').fill('540');
	await page.locator('input[name="tdsPercent"]').fill('1.3');
	await expect(page.locator('.ey')).not.toHaveText('—');
	await page.getByRole('button', { name: 'Complexity 4', exact: true }).click();
	await page.getByRole('button', { name: 'Bitterness 3.5', exact: true }).click();
	await page.getByRole('button', { name: 'Mouthfeel 4', exact: true }).click();
	await page.locator('textarea[name="tastingNotes"]').fill('e2e cup — apricot jam');
	await page.getByRole('button', { name: 'Complete', exact: true }).click();

	await page.waitForURL(new RegExp(`/log/${id}`));
	await expect(page.getByText(`Cup ${id.padStart(3, '0')}`, { exact: true })).toBeVisible();
	await expect(page.getByText('e2e cup — apricot jam')).toBeVisible();
	await expect(page.locator('.totals')).toContainText('3.8');
});

test('a reload mid-brew resumes the wall-clock timer', async ({ page }) => {
	await planAndStart(page);
	await page.keyboard.press('Space');
	await expect(page.locator('.events li').filter({ hasText: 'Bloom' })).toBeVisible();
	await page.waitForTimeout(1500);

	await page.reload();
	await expect(page.locator('.events li').filter({ hasText: 'Bloom' })).toBeVisible();
	const shown = await page.locator('.timer').innerText();
	const [m, s] = shown.split(':').map(Number);
	expect(m * 60 + s).toBeGreaterThanOrEqual(1);
	await expect(page.locator('.live')).toBeVisible();
});

test('the manual escape hatch records a brew without the timer', async ({ page }) => {
	const id = await planAndStart(page);
	await page.getByText('skip timer, type times').click();
	await page.waitForURL(`/brew/${id}/taste?manual=1`);
	await page.locator('input[name="totalTime"]').fill('2:45');
	await page.locator('input[name="tdsPercent"]').fill('1.22');
	await page.getByRole('button', { name: 'Complete', exact: true }).click();
	await page.waitForURL(new RegExp(`/log/${id}`));
	await expect(page.getByText('2:45')).toBeVisible();
});
