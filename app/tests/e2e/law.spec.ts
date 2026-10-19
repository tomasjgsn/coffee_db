import { expect, test, type Page } from '@playwright/test';

/**
 * Part III design law, checked on the rendered screens: no em dashes in
 * app copy, small red text in ember, zone colours only inside readings,
 * solar red only for the latest cup, no stamp, nothing animating idly.
 */

const SOLAR = ['rgb(222, 43, 27)', 'rgb(255, 77, 46)'];
const AMBER = 'rgb(232, 163, 61)';
const OLIVE = 'rgb(107, 124, 63)';
const GOLD = 'rgb(201, 162, 39)';

// Tomas's own words (notes, bean names typed into forms) are his to punctuate.
const USER_TEXT = 'textarea, .notes, .bag-notes, .note, .general-notes, option';

async function planAndStart(page: Page): Promise<string> {
	await page.goto('/brew');
	await expect(page.locator('input[name="doseG"]')).not.toHaveValue('0');
	await page.getByRole('button', { name: 'Start brew' }).click();
	await page.waitForURL(/\/brew\/\d+\/live/);
	return /\/brew\/(\d+)\/live/.exec(page.url())![1];
}

/** Visible app copy, excluding user-entered text. */
function appCopy(page: Page): Promise<string[]> {
	return page.evaluate((skip) => {
		const out: string[] = [];
		const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
		for (let n = walker.nextNode(); n; n = walker.nextNode()) {
			const el = n.parentElement;
			if (!el || el.closest(skip) || el.closest('script, style')) continue;
			const text = n.textContent?.trim();
			if (text && el.getClientRects().length > 0) out.push(text);
		}
		// Selects show their chosen option; check every option label too.
		for (const o of document.querySelectorAll('option')) out.push(o.textContent ?? '');
		return out;
	}, USER_TEXT);
}

/** Text elements under 24px set in solar red. */
function smallSolarText(page: Page): Promise<string[]> {
	return page.evaluate((solar) => {
		return [...document.querySelectorAll('body *')]
			.filter((el) => {
				const own = [...el.childNodes].some((c) => c.nodeType === 3 && c.textContent?.trim());
				if (!own || el.getClientRects().length === 0) return false;
				const cs = getComputedStyle(el);
				return solar.includes(cs.color) && parseFloat(cs.fontSize) < 24;
			})
			.map((el) => `${el.className}: ${el.textContent?.trim().slice(0, 20)}`);
	}, SOLAR);
}

test.describe('copy law', () => {
	test('no em dashes, raw zone codes or stray middots in app copy', async ({ page }) => {
		const id = await planAndStart(page);
		await page.keyboard.press('Space');
		await expect(page.locator('.events li')).toHaveCount(1);
		const routes = ['/', '/brew', '/log', '/log/16', '/log/21', '/chart', '/shelf', `/brew/${id}/taste`, `/brew/${id}/live`];
		for (const route of routes) {
			await page.goto(route);
			await page.waitForLoadState('networkidle');
			const copy = await appCopy(page);
			expect(copy.filter((t) => t.includes('—')), `em dashes on ${route}`).toEqual([]);
			expect(copy.filter((t) => /\b(Ideal|Under|Over)-(Ideal|Weak|Strong)\b/i.test(t)), `raw zones on ${route}`).toEqual([]);
			expect(copy.filter((t) => /\b1 brews\b|best \d\.\d{2,}/.test(t)), `counts on ${route}`).toEqual([]);
		}
		await page.goto('/');
		await expect(page.locator('header .meta')).not.toContainText('·');
		await expect(page.locator('header .meta')).not.toContainText('single user');
		await page.goto(`/brew/${id}/live`);
		await expect(page.locator('.controls')).not.toContainText('·');
	});

	test('a missing reading says what is missing', async ({ page }) => {
		await page.goto('/log/16');
		await expect(page.locator('.tds-ey')).toContainText('no tds');
		await expect(page.locator('.totals')).toContainText('unscored');
	});
});

test.describe('colour law', () => {
	test('small red text is ember, never solar', async ({ page }) => {
		const id = await planAndStart(page);
		await page.keyboard.press('Space');
		await expect(page.locator('.events li')).toHaveCount(1);
		for (const route of ['/brew', `/brew/${id}/live`, '/log/21', '/design']) {
			await page.goto(route);
			await page.waitForLoadState('networkidle');
			expect(await smallSolarText(page), `small solar text on ${route}`).toEqual([]);
		}
	});

	test('amber and olive stay inside readings', async ({ page }) => {
		await planAndStart(page);
		await page.goto('/');
		const draft = page.locator('.draft').first();
		expect(await draft.evaluate((el) => getComputedStyle(el).borderLeftColor)).not.toBe(AMBER);
		expect(await draft.locator('.lamp').evaluate((el) => getComputedStyle(el).backgroundImage)).not.toContain(AMBER.slice(4, -1));

		await page.goto('/brew');
		const dose = page.locator('input[name="doseG"]');
		await dose.fill(String(Number(await dose.inputValue()) + 1));
		await expect(dose).toHaveClass(/changed/);
		const changed = await dose.evaluate((el) => {
			const cs = getComputedStyle(el);
			return [cs.borderBottomColor, cs.backgroundColor];
		});
		expect(changed).not.toContain(AMBER);
		expect(changed).not.toContain('rgb(250, 238, 218)');

		await page.goto('/shelf');
		const tag = page.locator('.process').first();
		expect(await tag.evaluate((el) => [getComputedStyle(el).color, getComputedStyle(el).borderTopColor])).not.toContain(OLIVE);
	});

	test('on the chart, solar marks only the latest cup and gold stays off the frame', async ({ page }) => {
		await page.goto('/chart');
		await page.locator('.chart-frame circle.dot').first().hover({ force: true });
		const solar = await page.evaluate((solar) => {
			const dots = document.querySelectorAll('.chart-frame circle.dot');
			const latest = dots[dots.length - 1];
			return [...document.querySelectorAll('.chart-frame svg *, .panels svg *')]
				.filter((el) => {
					const cs = getComputedStyle(el);
					return solar.includes(cs.fill) || solar.includes(cs.stroke);
				})
				.map((el) => (el === latest ? 'latest cup' : `${el.tagName} ${el.getAttribute('class') ?? ''}`));
		}, SOLAR);
		expect(solar).toEqual(['latest cup']);

		const gold = await page.evaluate((gold) => {
			return [...document.querySelectorAll('.chart-frame, .chart-frame > span')].filter((el) =>
				[getComputedStyle(el, '::before'), getComputedStyle(el, '::after'), getComputedStyle(el)].some(
					(cs) => cs.backgroundColor === gold
				)
			).length;
		}, GOLD);
		expect(gold).toBe(0);
	});
});

test.describe('light and motion law', () => {
	test('completing a cup lands on the record without a stamp', async ({ page }) => {
		const id = await planAndStart(page);
		await page.goto(`/brew/${id}/taste?manual=1`);
		await page.locator('input[name="tdsPercent"]').fill('1.25');
		await page.getByRole('button', { name: 'Complete', exact: true }).click();
		await page.waitForURL(new RegExp(`/log/${id}$`));
		await expect(page.locator('.logged')).toHaveCount(0);
	});

	test('the extraction fringe resolves once instead of drifting', async ({ page }) => {
		const id = await planAndStart(page);
		await page.goto(`/brew/${id}/taste`);
		await page.locator('input[name="mugWeightG"]').fill('300');
		await page.locator('input[name="finalCombinedWeightG"]').fill('540');
		await page.locator('input[name="tdsPercent"]').fill('1.3');
		const fringe = page.locator('.fringe');
		await expect(fringe).toBeVisible();
		const anim = await fringe.evaluate((el) => {
			const cs = getComputedStyle(el);
			return [cs.animationIterationCount, parseFloat(cs.animationDuration) * 1000];
		});
		expect(anim[0]).toBe('1');
		expect(anim[1]).toBeLessThanOrEqual(240);
	});

	test('reduced motion: page changes run no animations', async ({ browser }) => {
		const context = await browser.newContext({ reducedMotion: 'reduce' });
		const page = await context.newPage();
		await page.goto('/');
		await page.locator('nav a[href="/log"]').click();
		await page.waitForURL(/\/log$/);
		const running = await page.evaluate(() =>
			document.getAnimations().filter((a) => a.playState === 'running').length
		);
		expect(running).toBe(0);
		await context.close();
	});
});

test.describe('record and layout', () => {
	test('the record draws half points as half dots', async ({ page }) => {
		await page.goto('/log/21');
		await expect(page.locator('.factor').filter({ hasText: 'Bitterness' }).locator('.dots')).toHaveText('●●●●◐');
	});

	test('shelf roast dates and the narrow masthead stay on one line', async ({ page }) => {
		await page.goto('/shelf');
		const lines = await page.locator('.stats dd').first().evaluate((el) => {
			const lh = parseFloat(getComputedStyle(el).lineHeight) || parseFloat(getComputedStyle(el).fontSize) * 1.2;
			return el.getBoundingClientRect().height / lh;
		});
		expect(lines).toBeLessThan(1.5);

		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/');
		const title = await page.locator('header h1').evaluate((el) => {
			return el.getBoundingClientRect().height / parseFloat(getComputedStyle(el).fontSize);
		});
		expect(title).toBeLessThan(1.5);
		expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
	});
});
