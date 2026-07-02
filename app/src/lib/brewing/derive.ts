import {
	brewRatio,
	brewScore,
	brewingZone,
	coffeeGramsPerLiter,
	daysSinceRoast,
	extractionCategory,
	extractionYield,
	overallRating,
	strengthCategory,
	type ExtractionCategory,
	type StrengthCategory
} from './calculations';

/**
 * Structural slices of the beans/brews rows. Kept free of $lib/server imports
 * so client-side components can derive values from loaded data; the Drizzle
 * row types satisfy these shapes automatically.
 */
export interface BrewLike {
	brewedAt: string;
	doseG: number | null;
	waterG: number | null;
	brewMassG: number | null;
	tdsPercent: number | null;
	scoreComplexity: number | null;
	scoreBitterness: number | null;
	scoreMouthfeel: number | null;
	legacy: string | null;
}

export interface BeanLike {
	purchaseDate: string | null;
}

export interface DerivedBrew {
	ratio: number | null;
	extractionYieldPercent: number | null;
	gramsPerLiter: number | null;
	strength: StrengthCategory | null;
	extraction: ExtractionCategory | null;
	zone: string | null;
	overall: number | null;
	brewScore: number | null;
	daysSinceRoast: number | null;
}

interface LegacyStored {
	score_overall_rating?: number | null;
}

/**
 * Compute every derived value for a brew. Mirrors process_single_brew.
 * Overall rating comes from the three factors; rows migrated from the
 * pre-three-factor era (brews 2-18) fall back to their stored legacy overall.
 */
export function deriveBrew(brew: BrewLike, bean?: BeanLike | null): DerivedBrew {
	const hasDose = brew.doseG !== null && brew.doseG > 0;
	const hasWater = brew.waterG !== null && brew.waterG > 0;

	const ratio = hasDose && hasWater ? brewRatio(brew.waterG!, brew.doseG!) : null;
	const gramsPerLiter = hasDose && hasWater ? coffeeGramsPerLiter(brew.doseG!, brew.waterG!) : null;

	const ey =
		hasDose && brew.brewMassG !== null && brew.tdsPercent !== null
			? extractionYield(brew.brewMassG, brew.tdsPercent, brew.doseG!)
			: null;

	const strength = brew.tdsPercent !== null ? strengthCategory(brew.tdsPercent) : null;
	const extraction = ey !== null ? extractionCategory(ey) : null;
	const zone = brew.tdsPercent !== null && ey !== null ? brewingZone(brew.tdsPercent, ey) : null;

	let overall = overallRating(brew.scoreComplexity, brew.scoreBitterness, brew.scoreMouthfeel);
	if (overall === null && brew.legacy) {
		const legacy = safeParseLegacy(brew.legacy);
		if (typeof legacy.score_overall_rating === 'number') overall = legacy.score_overall_rating;
	}

	const score = zone !== null ? brewScore(overall, zone) : null;

	return {
		ratio,
		extractionYieldPercent: ey,
		gramsPerLiter,
		strength,
		extraction,
		zone,
		overall,
		brewScore: score,
		daysSinceRoast: daysSinceRoast(brew.brewedAt, bean?.purchaseDate ?? null)
	};
}

function safeParseLegacy(raw: string): LegacyStored {
	try {
		return JSON.parse(raw) as LegacyStored;
	} catch {
		return {};
	}
}
