import { expect, test, type Locator, type Page } from '@playwright/test';

/**
 * Mid-brew ergonomics: the space bar always captures, held keys and
 * chords never do, the clock stops at drawdown, scores need no precision,
 * and every control a wet hand reaches for is big enough and shows focus.
 */

async function planAndStart(page: Page): Promise<string> {
	await page.goto('/brew');
	await expect(page.locator('input[name="doseG"]')).not.toHaveValue('0');
	await page.getByRole('button', { name: 'Start brew' }).click();
	await page.waitForURL(/\/brew\/\d+\/live/);
	return /\/brew\/(\d+)\/live/.exec(page.url())![1];
}

const eventTypes = (page: Page) => page.locator('.events li .type');

/** Every point of a centred min×min box (or the element itself, if larger) hits the element. */
async function expectHitArea(locator: Locator, min = 40) {
	await locator.scrollIntoViewIfNeeded();
	const misses = await locator.evaluate((el, min) => {
		const r = el.getBoundingClientRect();
		const cx = r.left + r.width / 2;
		const cy = r.top + r.height / 2;
		const hw = Math.max(r.width, min) / 2 - 1;
		const hh = Math.max(r.height, min) / 2 - 1;
		const points = [
			[cx, cy - hh],
			[cx, cy + hh],
			[cx - hw, cy],
			[cx + hw, cy]
		];
		return points
			.map(([x, y]) => ({ x, y, hit: document.elementFromPoint(x, y) }))
			.filter(({ hit }) => !hit || !(hit === el || el.contains(hit)))
			.map(
				({ x, y, hit }) =>
					`${Math.round(x)},${Math.round(y)} of box ${[r.left, r.top, r.width, r.height].map(Math.round)} hit ${hit?.outerHTML.slice(0, 60)}`
			);
	}, min);
	expect(misses, `hit area of ${await locator.evaluate((el) => el.outerHTML.slice(0, 80))}`).toEqual([]);
}

test.describe('live capture', () => {
	test('space after a pour end starts the next pour without typing grams', async ({ page }) => {
		await planAndStart(page);
		await page.keyboard.press('Space');
		await expect(eventTypes(page)).toHaveText(['Bloom']);
		await expect(page.locator('.controls')).toContainText('end bloom');

		await page.keyboard.press('Space');
		await expect(page.getByLabel('Water at this point, grams')).toBeFocused();

		await page.keyboard.press('Space');
		await expect(eventTypes(page)).toHaveText(['Bloom', 'Bloom end', 'Pour']);
	});

	test('grams typed into the scale field are kept when space starts the next pour', async ({ page }) => {
		await planAndStart(page);
		await page.keyboard.press('Space');
		await expect(eventTypes(page)).toHaveText(['Bloom']);
		await page.keyboard.press('Space');
		await expect(page.getByLabel('Water at this point, grams')).toBeFocused();

		await page.keyboard.type('54');
		await page.keyboard.press('Space');
		await expect(eventTypes(page)).toHaveText(['Bloom', 'Bloom end', 'Pour']);
		await expect(page.locator('.events li').nth(1)).toContainText('54 g');
	});

	test('a held space bar and modifier chords add no events', async ({ page }) => {
		await planAndStart(page);
		// First keydown starts the clock and the bloom; the auto-repeats that follow must not.
		await page.keyboard.down('Space');
		await page.keyboard.down('Space');
		await page.keyboard.down('Space');
		await page.keyboard.down('Space');
		await page.keyboard.up('Space');
		await page.keyboard.press('Meta+s');
		await page.keyboard.press('Control+d');
		await page.waitForTimeout(500);
		await expect(eventTypes(page)).toHaveText(['Bloom']);
	});

	test('the clock stops at the drawdown', async ({ page }) => {
		await planAndStart(page);
		await page.keyboard.press('Space');
		await expect(eventTypes(page)).toHaveText(['Bloom']);
		await page.keyboard.press('d');
		await expect(eventTypes(page)).toHaveText(['Bloom', 'Drawdown done']);

		const drawdownAt = await page.locator('.events li').nth(1).locator('.at').innerText();
		await page.waitForTimeout(2200);
		await expect(page.locator('.digits')).toHaveText(drawdownAt);
	});
});

test.describe('taste scoring', () => {
	test('each score dot is one 32px target that cycles full, half, clear', async ({ page }) => {
		const id = await planAndStart(page);
		await page.goto(`/brew/${id}/taste`);

		const dot = page.getByRole('button', { name: 'Complexity 4', exact: true });
		const box = (await dot.boundingBox())!;
		expect(box.width).toBeGreaterThanOrEqual(32);
		expect(box.height).toBeGreaterThanOrEqual(32);

		const value = page.locator('input[name="scoreComplexity"]');
		await dot.click();
		await expect(value).toHaveValue('4');
		await dot.click();
		await expect(value).toHaveValue('3.5');
		await dot.click();
		await expect(value).toHaveValue('');
	});

	test('digit and arrow keys score a focused factor', async ({ page }) => {
		const id = await planAndStart(page);
		await page.goto(`/brew/${id}/taste`);

		const slider = page.getByRole('slider', { name: 'Mouthfeel score' });
		const value = page.locator('input[name="scoreMouthfeel"]');
		await slider.focus();
		await page.keyboard.press('3');
		await expect(value).toHaveValue('3');
		await page.keyboard.press('ArrowRight');
		await expect(value).toHaveValue('3.5');
		await expect(slider).toHaveAttribute('aria-valuenow', '3.5');
		await page.keyboard.press('0');
		await expect(value).toHaveValue('');
	});
});

test.describe('targets and focus', () => {
	test('mid-brew links and keys are at least 40px to hit', async ({ page }) => {
		await planAndStart(page);
		await expectHitArea(page.locator('.skip'));
		for (const link of await page.locator('nav[aria-label="Primary"] a').all()) {
			await expectHitArea(link);
		}

		await page.keyboard.press('Space');
		await expect(eventTypes(page)).toHaveText(['Bloom']);
		for (const key of await page.locator('.controls .key').all()) {
			await expectHitArea(key);
		}

		await page.goto('/');
		const draft = page.locator('.draft').first();
		await expectHitArea(draft.locator('a.resume').first());
		await expectHitArea(draft.locator('a.resume.taste'));
	});

	test('keyboard focus is visible on links and on the plan cards', async ({ page }) => {
		await page.goto('/brew');
		await page.keyboard.press('Tab');
		const ring = (el: Element) => {
			const cs = getComputedStyle(el);
			return `${cs.outlineStyle} ${cs.outlineWidth}`;
		};
		await expect.poll(() => page.evaluate(() => document.activeElement?.closest('nav') !== null)).toBe(true);
		expect(await page.evaluate(`(${ring.toString()})(document.activeElement)`)).toBe('solid 2px');

		const tabUntil = async (selector: string) => {
			for (let i = 0; i < 20; i++) {
				if (await page.evaluate((s) => !!document.activeElement?.closest(s), selector)) return;
				await page.keyboard.press('Tab');
			}
			throw new Error(`focus never reached ${selector}`);
		};
		await tabUntil('.bag-card');
		expect(await page.evaluate(`(${ring.toString()})(document.activeElement.closest('.bag-card'))`)).toBe('solid 2px');
		await tabUntil('.method-card');
		expect(await page.evaluate(`(${ring.toString()})(document.activeElement.closest('.method-card'))`)).toBe('solid 2px');
	});

	test('chart cups are reachable by keyboard', async ({ page }) => {
		await page.goto('/chart');
		for (let i = 0; i < 20; i++) {
			if (await page.evaluate(() => document.activeElement?.matches('circle.dot') ?? false)) break;
			await page.keyboard.press('Tab');
		}
		await expect(page.locator('circle.dot:focus')).toHaveCount(1);
		const card = page.locator('.card[role="tooltip"]');
		await expect(card).toBeVisible();
		const first = await card.locator('.corners').innerText();

		await page.keyboard.press('ArrowLeft');
		await expect(card.locator('.corners')).not.toHaveText(first);

		await page.keyboard.press('Enter');
		await expect(page.getByRole('link', { name: 'Open cup' })).toBeVisible();
	});
});

test.describe('plan picker', () => {
	test('recent bags come first and the rest fold away', async ({ page }) => {
		await page.goto('/brew');
		const recent = page.locator('.bags.recent .bag-card');
		await expect(recent).toHaveCount(4);
		await expect(recent.first()).toHaveClass(/selected/);

		const other = page.locator('details.other-bags');
		await expect(other.locator('summary')).toHaveText(/^other bags \(\d+\)$/);
		await expect(other.locator('.bag-card').first()).toBeHidden();

		await other.locator('summary').click();
		const older = other.locator('.bag-card').first();
		await older.click();
		await expect(older).toHaveClass(/selected/);
	});
});
