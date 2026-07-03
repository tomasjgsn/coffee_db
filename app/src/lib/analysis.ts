/** Tiny statistics for the chart's learning panels. Pure, no dependencies. */

export interface Fit {
	slope: number;
	intercept: number;
	/** Pearson correlation; 0 when y has no variance. */
	r: number;
	n: number;
}

export function leastSquares(points: { x: number; y: number }[]): Fit | null {
	const n = points.length;
	if (n < 2) return null;

	const meanX = points.reduce((s, p) => s + p.x, 0) / n;
	const meanY = points.reduce((s, p) => s + p.y, 0) / n;

	let sxx = 0;
	let syy = 0;
	let sxy = 0;
	for (const p of points) {
		const dx = p.x - meanX;
		const dy = p.y - meanY;
		sxx += dx * dx;
		syy += dy * dy;
		sxy += dx * dy;
	}
	if (sxx === 0) return null;

	const slope = sxy / sxx;
	const intercept = meanY - slope * meanX;
	const r = syy === 0 ? 0 : sxy / Math.sqrt(sxx * syy);
	return { slope, intercept, r, n };
}

export type TrendDirection = 'up' | 'down' | 'flat';

/**
 * A direction is only worth showing with enough cups (≥ minN) — and only an
 * arrow when the correlation is meaningful (|r| ≥ minR); otherwise 'flat'.
 */
export function trendDirection(fit: Fit | null, minN = 6, minR = 0.25): TrendDirection | null {
	if (!fit || fit.n < minN) return null;
	if (Math.abs(fit.r) < minR) return 'flat';
	return fit.slope > 0 ? 'up' : 'down';
}
