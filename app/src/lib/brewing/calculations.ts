/**
 * Brewing science calculations, ported 1:1 from the Python originals in
 * src/models/brewing_calculations.py and src/processing/process_entry_data.py.
 * Formulas, thresholds, and rounding must stay identical so the 61 historical
 * brews keep their derived values — the golden migration test enforces this.
 */

export const STRENGTH_THRESHOLDS = { weakMax: 1.15, idealMax: 1.35 } as const;
export const EXTRACTION_THRESHOLDS = { underMax: 18.0, idealMax: 22.0 } as const;

export type StrengthCategory = 'Weak' | 'Ideal' | 'Strong';
export type ExtractionCategory = 'Under' | 'Ideal' | 'Over';

/**
 * CPython's round(): round-half-to-even evaluated on the true decimal value
 * of the double. Naive `Math.round(x * 10**n) / 10**n` disagrees on exact
 * binary halves (18.25 → JS 18.3, Python 18.2) and on doubles that sit just
 * below a half (6.55 → Python 6.5). toFixed gives us a correctly-rounded
 * decimal expansion long enough to make both calls exactly.
 */
export function pyRound(value: number, ndigits = 0): number {
	if (!Number.isFinite(value)) return value;
	const sign = value < 0 ? -1 : 1;
	const digits = Math.abs(value).toFixed(Math.min(100, ndigits + 25));
	const dot = digits.indexOf('.');
	const intPart = digits.slice(0, dot);
	const fracPart = digits.slice(dot + 1);

	const keep = fracPart.slice(0, ndigits);
	const rest = fracPart.slice(ndigits);

	let roundUp: boolean;
	const restTrimmed = rest.replace(/0+$/, '');
	if (restTrimmed === '' || restTrimmed < '5') {
		roundUp = false;
	} else if (restTrimmed > '5') {
		roundUp = true;
	} else {
		const lastKept = ndigits === 0 ? intPart.slice(-1) : keep.slice(-1) || '0';
		roundUp = Number(lastKept) % 2 === 1;
	}

	let result = Number(`${intPart}${keep ? '.' + keep : ''}`);
	if (roundUp) result += Math.pow(10, -ndigits);
	return sign * pyRoundFix(result, ndigits);
}

/** Clean float noise introduced by the 10^-n increment (e.g. 18.2 + 0.1). */
function pyRoundFix(value: number, ndigits: number): number {
	return Number(value.toFixed(Math.max(0, ndigits)));
}

/** water:coffee ratio, e.g. 300/18 → 16.7. */
export function brewRatio(waterMl: number, doseGrams: number): number {
	if (doseGrams === 0) throw new Error('Cannot calculate brew ratio: dose is zero');
	return pyRound(waterMl / doseGrams, 1);
}

/** Extraction yield % = (brew mass × TDS%) / dose. UC Davis standard. */
export function extractionYield(brewMassGrams: number, tdsPercent: number, doseGrams: number): number {
	if (doseGrams === 0) throw new Error('Cannot calculate extraction yield: dose is zero');
	return pyRound((brewMassGrams * tdsPercent) / doseGrams, 2);
}

export function coffeeGramsPerLiter(doseGrams: number, waterMl: number): number {
	if (waterMl === 0) throw new Error('Cannot calculate grams per liter: water is zero');
	return pyRound((doseGrams / waterMl) * 1000, 1);
}

export function strengthCategory(tdsPercent: number): StrengthCategory {
	if (tdsPercent < STRENGTH_THRESHOLDS.weakMax) return 'Weak';
	if (tdsPercent <= STRENGTH_THRESHOLDS.idealMax) return 'Ideal';
	return 'Strong';
}

export function extractionCategory(extractionYieldPercent: number): ExtractionCategory {
	if (extractionYieldPercent < EXTRACTION_THRESHOLDS.underMax) return 'Under';
	if (extractionYieldPercent <= EXTRACTION_THRESHOLDS.idealMax) return 'Ideal';
	return 'Over';
}

export function brewingZone(tdsPercent: number, extractionYieldPercent: number): string {
	return `${extractionCategory(extractionYieldPercent)}-${strengthCategory(tdsPercent)}`;
}

/** Composite score: 60% rating + 40% zone bonus (10 / 7 / 4). */
export function brewScore(overall: number | null | undefined, zone: string): number | null {
	if (overall === null || overall === undefined || Number.isNaN(overall)) return null;
	let bonus: number;
	if (zone === 'Ideal-Ideal') bonus = 10;
	else if (zone.includes('Ideal')) bonus = 7;
	else bonus = 4;
	return pyRound(overall * 0.6 + bonus * 0.4, 1);
}

/** Three-factor overall = mean(complexity, bitterness, mouthfeel), 3 dp. */
export function overallRating(
	complexity: number | null | undefined,
	bitterness: number | null | undefined,
	mouthfeel: number | null | undefined
): number | null {
	if (
		complexity === null || complexity === undefined || Number.isNaN(complexity) ||
		bitterness === null || bitterness === undefined || Number.isNaN(bitterness) ||
		mouthfeel === null || mouthfeel === undefined || Number.isNaN(mouthfeel)
	) {
		return null;
	}
	return pyRound((complexity + bitterness + mouthfeel) / 3, 3);
}

/** Whole days between ISO dates; negative or missing → null. */
export function daysSinceRoast(brewDate: string | null, purchaseDate: string | null): number | null {
	if (!brewDate || !purchaseDate) return null;
	const brew = isoToUtcMs(brewDate);
	const purchase = isoToUtcMs(purchaseDate);
	if (brew === null || purchase === null) return null;
	const days = Math.round((brew - purchase) / 86_400_000);
	return days < 0 ? null : days;
}

function isoToUtcMs(iso: string): number | null {
	const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso.trim());
	if (!m) return null;
	return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
}

/**
 * Date parsing per CoffeeDataProcessor._parse_date: ISO YYYY-MM-DD (standard),
 * legacy D/M/YY with a 2000s pivot at 30, ISO datetime. Blank → null.
 */
export function parseFlexibleDate(value: string | null | undefined): string | null {
	if (value === null || value === undefined) return null;
	const trimmed = String(value).trim();
	if (trimmed === '') return null;

	const iso = /^(\d{4})-(\d{2})-(\d{2})(?:[ T]\d{2}:\d{2}:\d{2})?$/.exec(trimmed);
	if (iso) return `${iso[1]}-${iso[2]}-${iso[3]}`;

	const legacy = /^(\d{1,2})\/(\d{1,2})\/(\d{2})$/.exec(trimmed);
	if (legacy) {
		const day = Number(legacy[1]);
		const month = Number(legacy[2]);
		const shortYear = Number(legacy[3]);
		const year = shortYear <= 30 ? 2000 + shortYear : 1900 + shortYear;
		return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
	}

	throw new Error(`Date must be YYYY-MM-DD or legacy D/M/YY. Received: ${trimmed}`);
}
