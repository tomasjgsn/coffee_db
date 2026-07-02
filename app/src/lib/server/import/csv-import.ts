import { parse } from 'csv-parse/sync';
import { eq } from 'drizzle-orm';
import type { Db } from '$lib/server/db';
import { beans, brews, type NewBean, type NewBrew } from '$lib/server/db/schema';
import { parseFlexibleDate } from '$lib/brewing/calculations';
import { methodForLegacyDevice } from '$lib/domain/methods';
import {
	CSV_COLUMNS,
	LEGACY_COLUMNS,
	METHOD_PARAM_COLUMNS,
	RETIRED_DEVICE_METHODS,
	UNKNOWN_METHOD,
	type CsvRow
} from '$lib/server/legacy-columns';

export interface ImportReport {
	brewsImported: number;
	beansCreated: number;
	warnings: string[];
}

/** '' → null, numeric strings → number, everything else stays a string. */
function parseValue(raw: string): string | number | null {
	const trimmed = raw.trim();
	if (trimmed === '') return null;
	const num = Number(trimmed);
	return Number.isFinite(num) && /^-?[\d.]+(e-?\d+)?$/i.test(trimmed) ? num : trimmed;
}

function num(row: CsvRow, col: (typeof CSV_COLUMNS)[number]): number | null {
	const value = parseValue(row[col]);
	return typeof value === 'number' ? value : null;
}

function str(row: CsvRow, col: (typeof CSV_COLUMNS)[number]): string | null {
	const trimmed = row[col].trim();
	return trimmed === '' ? null : trimmed;
}

function methodForDevice(device: string | null): { method: string; warning?: string } {
	if (!device) return { method: UNKNOWN_METHOD, warning: 'row has no brew_device' };
	const registered = methodForLegacyDevice(device);
	if (registered) return { method: registered.id };
	if (device in RETIRED_DEVICE_METHODS) return { method: RETIRED_DEVICE_METHODS[device] };
	return {
		method: UNKNOWN_METHOD,
		warning: `unrecognized brew_device "${device}" mapped to ${UNKNOWN_METHOD}`
	};
}

function beanKey(row: CsvRow): string {
	return `${row.bean_name.trim()}|${row.bean_roast_date.trim()}`;
}

function jsonFromColumns(row: CsvRow, columns: readonly (typeof CSV_COLUMNS)[number][]): string | null {
	const out: Record<string, string | number> = {};
	for (const col of columns) {
		const value = parseValue(row[col]);
		if (value !== null) out[col] = value;
	}
	return Object.keys(out).length > 0 ? JSON.stringify(out) : null;
}

/** Import the legacy cups_of_coffee.csv into a fresh database. */
export function importCsv(db: Db, csvText: string): ImportReport {
	const rows = parse(csvText, { columns: true, skip_empty_lines: true }) as CsvRow[];
	const warnings: string[] = [];
	const now = new Date().toISOString();

	const header = Object.keys(rows[0] ?? {});
	for (const col of CSV_COLUMNS) {
		if (!header.includes(col)) warnings.push(`missing expected column: ${col}`);
	}

	const beanIds = new Map<string, number>();
	let beansCreated = 0;
	let brewsImported = 0;

	for (const row of rows) {
		// Legacy rows 26/27 have no bean name; Python's NaN grouping gave them
		// no bean statistics. They stay bean-less rather than becoming a phantom bag.
		const hasBean = row.bean_name.trim() !== '';
		if (!hasBean) warnings.push(`brew ${row.brew_id}: no bean_name, imported without a bean`);

		const key = beanKey(row);
		let beanId = hasBean ? beanIds.get(key) : undefined;
		if (beanId !== undefined) {
			mergeFillBean(db, beanId, row);
		}
		if (hasBean && beanId === undefined) {
			const bean: NewBean = {
				name: row.bean_name.trim(),
				originCountry: str(row, 'bean_origin_country'),
				originRegion: str(row, 'bean_origin_region'),
				variety: str(row, 'bean_variety'),
				process: str(row, 'bean_process_method'),
				roastDate: parseFlexibleDate(str(row, 'bean_roast_date')),
				roastLevel: str(row, 'bean_roast_level'),
				purchaseDate: parseFlexibleDate(str(row, 'bean_purchase_date')),
				bagSizeG: num(row, 'estimated_bag_size_grams'),
				notes: str(row, 'bean_notes'),
				archived: false,
				createdAt: now,
				updatedAt: now
			};
			const inserted = db.insert(beans).values(bean).returning({ id: beans.id }).get();
			beanId = inserted.id;
			beanIds.set(key, beanId);
			beansCreated += 1;
		}

		const device = str(row, 'brew_device');
		const { method, warning } = methodForDevice(device);
		if (warning) warnings.push(`brew ${row.brew_id}: ${warning}`);

		const brewedAt = parseFlexibleDate(str(row, 'brew_date'));
		if (!brewedAt) {
			warnings.push(`brew ${row.brew_id}: missing brew_date, skipped`);
			continue;
		}

		const brew: NewBrew = {
			id: num(row, 'brew_id') ?? undefined,
			beanId: beanId ?? null,
			brewedAt,
			method,
			status: 'complete',
			archived: str(row, 'archive_status') === 'archived',
			grinder: str(row, 'grind_model'),
			grindSize: num(row, 'grind_size'),
			doseG: num(row, 'coffee_dose_grams'),
			waterG: num(row, 'water_volume_ml'),
			tempC: num(row, 'water_temp_degC'),
			hotWaterG: null,
			iceG: null,
			mugWeightG: num(row, 'mug_weight_grams'),
			finalCombinedWeightG: num(row, 'final_combined_weight_grams'),
			brewMassG: num(row, 'final_brew_mass_grams'),
			tdsPercent: num(row, 'final_tds_percent'),
			totalTimeS: num(row, 'brew_total_time_s'),
			scoreComplexity: num(row, 'score_complexity'),
			scoreBitterness: num(row, 'score_bitterness'),
			scoreMouthfeel: num(row, 'score_mouthfeel'),
			flavorProfile: str(row, 'score_flavor_profile_category'),
			tastingNotes: str(row, 'score_notes'),
			notes: str(row, 'notes'),
			methodParams: jsonFromColumns(row, METHOD_PARAM_COLUMNS),
			legacy: jsonFromColumns(row, LEGACY_COLUMNS),
			createdAt: now,
			updatedAt: now
		};
		db.insert(brews).values(brew).run();
		brewsImported += 1;
	}

	return { brewsImported, beansCreated, warnings };
}

/**
 * Bean rows repeat per brew in the legacy CSV; later brews sometimes carry
 * fields the first one left blank. Fill gaps, never overwrite.
 */
function mergeFillBean(db: Db, beanId: number, row: CsvRow): void {
	const existing = db.select().from(beans).where(eq(beans.id, beanId)).get();
	if (!existing) return;
	const fills: Partial<NewBean> = {};
	if (existing.originCountry === null) {
		const v = str(row, 'bean_origin_country');
		if (v) fills.originCountry = v;
	}
	if (existing.originRegion === null) {
		const v = str(row, 'bean_origin_region');
		if (v) fills.originRegion = v;
	}
	if (existing.variety === null) {
		const v = str(row, 'bean_variety');
		if (v) fills.variety = v;
	}
	if (existing.process === null) {
		const v = str(row, 'bean_process_method');
		if (v) fills.process = v;
	}
	if (existing.roastLevel === null) {
		const v = str(row, 'bean_roast_level');
		if (v) fills.roastLevel = v;
	}
	if (existing.purchaseDate === null) {
		const v = parseFlexibleDate(str(row, 'bean_purchase_date'));
		if (v) fills.purchaseDate = v;
	}
	if (existing.bagSizeG === null) {
		const v = num(row, 'estimated_bag_size_grams');
		if (v !== null) fills.bagSizeG = v;
	}
	if (existing.notes === null) {
		const v = str(row, 'bean_notes');
		if (v) fills.notes = v;
	}
	if (Object.keys(fills).length > 0) {
		db.update(beans)
			.set({ ...fills, updatedAt: new Date().toISOString() })
			.where(eq(beans.id, beanId))
			.run();
	}
}
