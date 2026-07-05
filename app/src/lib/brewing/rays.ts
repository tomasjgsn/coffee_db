/**
 * Iso-ratio ray geometry for the brewing control chart.
 *
 * Because EY = brew_mass × TDS / dose, every cup satisfies
 * TDS / EY = dose / brew_mass — a straight ray from the chart's origin.
 * Grind, temperature, and time move a cup ALONG its ray; only the recipe
 * (ratio and water retention) moves it BETWEEN rays. The Ideal-Ideal box is
 * reachable only for slopes between BOX_SLOPES.min and BOX_SLOPES.max.
 *
 * Advisory/display math only — the frozen scoring formulas live in
 * calculations.ts and are untouched (golden test enforced).
 */

import { EXTRACTION_THRESHOLDS, STRENGTH_THRESHOLDS, pyRound } from './calculations';

export const BOX_SLOPES = {
	/** Flattest ray that still clips the box: weak-max TDS over ideal-max EY. */
	min: STRENGTH_THRESHOLDS.weakMax / EXTRACTION_THRESHOLDS.idealMax,
	/** Steepest ray that still clips the box: ideal-max TDS over under-max EY. */
	max: STRENGTH_THRESHOLDS.idealMax / EXTRACTION_THRESHOLDS.underMax
} as const;

/** The ray a finished cup sits on: TDS per EY point. */
export function raySlope(doseG: number, brewMassG: number): number {
	return doseG / brewMassG;
}

export type RayClass = 'above' | 'through' | 'below';

export function classifyRay(slope: number): RayClass {
	if (slope > BOX_SLOPES.max) return 'above';
	if (slope < BOX_SLOPES.min) return 'below';
	return 'through';
}

/**
 * Predicted slope for a planned brew: brew mass ≈ water − LRR × dose, so
 * slope = dose / (water − LRR·dose) = 1 / (ratio − LRR).
 */
export function slopeForRatio(ratio: number, lrr: number): number | null {
	const denominator = ratio - lrr;
	if (denominator <= 0) return null;
	return 1 / denominator;
}

/** Ratios whose rays pass through the ideal box, for a given retention. */
export function ratioWindowForBox(lrr: number): { min: number; max: number } {
	return { min: lrr + 1 / BOX_SLOPES.max, max: lrr + 1 / BOX_SLOPES.min };
}

/** Water the grounds kept, per gram of coffee, measured from a finished cup. */
export function liquidRetainedRatio(
	doseG: number | null,
	waterG: number | null,
	brewMassG: number | null
): number | null {
	if (!doseG || doseG <= 0 || waterG === null || brewMassG === null) return null;
	return (waterG - brewMassG) / doseG;
}

/**
 * Immersion-mode extraction reading (Rao/Gagné convention): retained slurry
 * liquid is at beverage strength, so the whole brew water counts.
 * Secondary display only — never feeds zones or scores.
 */
export function immersionEY(
	tdsPercent: number | null,
	waterG: number | null,
	doseG: number | null
): number | null {
	if (tdsPercent === null || waterG === null || !doseG || doseG <= 0) return null;
	return pyRound((tdsPercent * waterG) / doseG, 2);
}
