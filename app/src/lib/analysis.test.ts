import { describe, expect, it } from 'vitest';
import { leastSquares, trendDirection } from './analysis';

describe('leastSquares', () => {
	it('fits a perfect positive line', () => {
		const fit = leastSquares([
			{ x: 1, y: 2 },
			{ x: 2, y: 4 },
			{ x: 3, y: 6 }
		]);
		expect(fit).not.toBeNull();
		expect(fit!.slope).toBeCloseTo(2, 6);
		expect(fit!.intercept).toBeCloseTo(0, 6);
		expect(fit!.r).toBeCloseTo(1, 6);
		expect(fit!.n).toBe(3);
	});

	it('fits a noisy negative relationship', () => {
		const fit = leastSquares([
			{ x: 90, y: 4.5 },
			{ x: 92, y: 4.2 },
			{ x: 94, y: 4.0 },
			{ x: 96, y: 3.6 },
			{ x: 98, y: 3.5 }
		]);
		expect(fit!.slope).toBeLessThan(0);
		expect(fit!.r).toBeLessThan(-0.9);
	});

	it('returns r=0 for a constant series', () => {
		const fit = leastSquares([
			{ x: 1, y: 3 },
			{ x: 2, y: 3 },
			{ x: 3, y: 3 }
		]);
		expect(fit!.slope).toBeCloseTo(0, 6);
		expect(fit!.r).toBe(0);
	});

	it('returns null for fewer than two points or zero x-variance', () => {
		expect(leastSquares([])).toBeNull();
		expect(leastSquares([{ x: 1, y: 1 }])).toBeNull();
		expect(
			leastSquares([
				{ x: 5, y: 1 },
				{ x: 5, y: 2 },
				{ x: 5, y: 3 }
			])
		).toBeNull();
	});
});

describe('trendDirection', () => {
	const upFit = { slope: 0.5, intercept: 0, r: 0.8, n: 10 };

	it('reports direction only with enough cups', () => {
		expect(trendDirection(upFit)).toBe('up');
		expect(trendDirection({ ...upFit, n: 5 })).toBeNull();
	});

	it('reports flat when correlation is weak', () => {
		expect(trendDirection({ ...upFit, r: 0.1 })).toBe('flat');
		expect(trendDirection({ ...upFit, slope: -0.5, r: -0.1 })).toBe('flat');
	});

	it('reports down for strong negative fits', () => {
		expect(trendDirection({ slope: -0.3, intercept: 5, r: -0.6, n: 8 })).toBe('down');
	});

	it('handles null fits', () => {
		expect(trendDirection(null)).toBeNull();
	});
});
