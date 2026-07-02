import { stringify } from 'csv-stringify/sync';
import { asc } from 'drizzle-orm';
import type { Db } from '$lib/server/db';
import { beans as beansTable, brews as brewsTable, type Bean, type Brew } from '$lib/server/db/schema';
import { deriveBrew } from '$lib/brewing/derive';
import { pyRound } from '$lib/brewing/calculations';
import { CSV_COLUMNS, type CsvColumn } from '$lib/server/legacy-columns';

type CellValue = string | number | null;

interface BeanStats {
	usageCount: number;
	avgRating: number | null;
	improvementVsLast: number | null;
}

/**
 * Reproduce data/cups_of_coffee.csv from the database: same 85 columns, same
 * order, derived fields recomputed by the TS calc lib, bookkeeping columns
 * spread back from legacy JSON. Written after every mutation so the CSV stays
 * the git-diffable record it has always been.
 */
export function exportCsv(db: Db): string {
	const allBeans = db.select().from(beansTable).all();
	const beansById = new Map<number, Bean>(allBeans.map((b) => [b.id, b]));
	const allBrews = db.select().from(brewsTable).orderBy(asc(brewsTable.id)).all();

	const stats = computeBeanStats(allBrews, beansById);

	const records = allBrews.map((brew) => {
		const bean = brew.beanId !== null ? (beansById.get(brew.beanId) ?? null) : null;
		return buildRow(brew, bean, stats.get(brew.id) ?? { usageCount: 0, avgRating: null, improvementVsLast: null });
	});

	return stringify(records, {
		header: true,
		columns: CSV_COLUMNS as unknown as string[],
		cast: {
			// eslint-disable-next-line @typescript-eslint/no-base-to-string
			object: (value) => String(value)
		}
	});
}

function legacyOf(brew: Brew): Record<string, string | number> {
	if (!brew.legacy) return {};
	try {
		return JSON.parse(brew.legacy) as Record<string, string | number>;
	} catch {
		return {};
	}
}

function paramsOf(brew: Brew): Record<string, string | number> {
	if (!brew.methodParams) return {};
	try {
		return JSON.parse(brew.methodParams) as Record<string, string | number>;
	} catch {
		return {};
	}
}

/**
 * Mirror of CoffeeDataProcessor._calculate_bean_statistics: groups by bean
 * NAME (not id), counts all brews of that bean, averages the rated ones, and
 * diffs against the previous brew in brew-date order (stable, ties by id).
 */
function computeBeanStats(allBrews: Brew[], beansById: Map<number, Bean>): Map<number, BeanStats> {
	const byName = new Map<string, Brew[]>();
	for (const brew of allBrews) {
		const bean = brew.beanId !== null ? beansById.get(brew.beanId) : undefined;
		// Bean-less brews get no statistics — same as pandas' NaN != NaN grouping.
		if (!bean?.name) continue;
		const group = byName.get(bean.name) ?? [];
		group.push(brew);
		byName.set(bean.name, group);
	}

	const overallOf = (brew: Brew): number | null =>
		deriveBrew(brew, brew.beanId !== null ? beansById.get(brew.beanId) : null).overall;

	const out = new Map<number, BeanStats>();
	for (const group of byName.values()) {
		const sorted = [...group].sort(
			(a, b) => a.brewedAt.localeCompare(b.brewedAt) || a.id - b.id
		);
		const ratings = sorted.map(overallOf);
		const rated = ratings.filter((r): r is number => r !== null);
		const avg = rated.length > 0 ? pyRound(rated.reduce((s, r) => s + r, 0) / rated.length, 1) : null;

		sorted.forEach((brew, i) => {
			let improvement: number | null = null;
			const current = ratings[i];
			if (sorted.length > 1 && current !== null && i > 0) {
				const previous = ratings[i - 1];
				if (previous !== null) improvement = pyRound(current - previous, 1);
			}
			out.set(brew.id, { usageCount: sorted.length, avgRating: avg, improvementVsLast: improvement });
		});
	}
	return out;
}

function buildRow(brew: Brew, bean: Bean | null, stats: BeanStats): Record<CsvColumn, CellValue> {
	const derived = deriveBrew(brew, bean);
	const legacy = legacyOf(brew);
	const params = paramsOf(brew);

	const row = {} as Record<CsvColumn, CellValue>;
	for (const col of CSV_COLUMNS) row[col] = null;

	// Bookkeeping + technique params spread back under their original names
	for (const [key, value] of Object.entries(legacy)) {
		if ((CSV_COLUMNS as readonly string[]).includes(key)) row[key as CsvColumn] = value;
	}
	for (const [key, value] of Object.entries(params)) {
		if ((CSV_COLUMNS as readonly string[]).includes(key)) row[key as CsvColumn] = value;
	}

	// Core columns from real fields
	row.brew_id = brew.id;
	row.brew_date = brew.brewedAt.slice(0, 10);
	if (bean) {
		row.bean_name = bean.name;
		row.bean_origin_country = bean.originCountry;
		row.bean_origin_region = bean.originRegion;
		row.bean_variety = bean.variety;
		row.bean_process_method = bean.process;
		row.bean_roast_date = bean.roastDate;
		row.bean_roast_level = bean.roastLevel;
		row.bean_notes = bean.notes;
		row.bean_purchase_date = bean.purchaseDate;
		row.estimated_bag_size_grams = bean.bagSizeG;
	}
	row.grind_size = brew.grindSize;
	row.grind_model = brew.grinder;
	row.coffee_dose_grams = brew.doseG;
	row.water_volume_ml = brew.waterG;
	row.water_temp_degC = brew.tempC;
	row.brew_total_time_s = brew.totalTimeS;
	row.final_tds_percent = brew.tdsPercent;
	row.final_brew_mass_grams = brew.brewMassG;
	row.mug_weight_grams = brew.mugWeightG;
	row.final_combined_weight_grams = brew.finalCombinedWeightG;
	row.score_complexity = brew.scoreComplexity;
	row.score_bitterness = brew.scoreBitterness;
	row.score_mouthfeel = brew.scoreMouthfeel;
	row.score_flavor_profile_category = brew.flavorProfile;
	row.score_notes = brew.tastingNotes;
	row.notes = brew.notes;

	// Derived fields — always recomputed, never read from storage
	row.score_overall_rating = derived.overall;
	row.beans_days_since_roast = derived.daysSinceRoast;
	row.brew_ratio_to_1 = derived.ratio;
	row.final_extraction_yield_percent = derived.extractionYieldPercent;
	row.coffee_grams_per_liter = derived.gramsPerLiter;
	row.score_strength_category = derived.strength;
	row.score_extraction_category = derived.extraction;
	row.score_brewing_zone = derived.zone;
	row.score_brew = derived.brewScore;
	row.bean_usage_count = stats.usageCount;
	row.score_avg_rating_this_bean = stats.avgRating;
	row.score_improvement_vs_last = stats.improvementVsLast;

	return row;
}
