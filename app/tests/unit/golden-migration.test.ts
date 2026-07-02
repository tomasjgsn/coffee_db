import { beforeAll, describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'csv-parse/sync';
import { openDb, type DbHandle } from '$lib/server/db';
import { beans, brews } from '$lib/server/db/schema';
import { importCsv, type ImportReport } from '$lib/server/import/csv-import';
import { exportCsv } from '$lib/server/export/csv-export';
import { deriveBrew } from '$lib/brewing/derive';
import { CSV_COLUMNS, type CsvColumn, type CsvRow } from '$lib/server/legacy-columns';
import { eq } from 'drizzle-orm';

/**
 * Golden migration test: the real cups_of_coffee.csv (61 brews) must import
 * losslessly, every derived field must recompute to exactly what the Python
 * pipeline stored, and the CSV export must round-trip value-identically.
 * The CSV is read as a fixture only — nothing here writes to data/.
 */

const CSV_PATH = join(
	dirname(fileURLToPath(import.meta.url)),
	'..',
	'..',
	'..',
	'data',
	'cups_of_coffee.csv'
);

let csvText: string;
let original: CsvRow[];
let handle: DbHandle;
let report: ImportReport;

beforeAll(() => {
	csvText = readFileSync(CSV_PATH, 'utf-8');
	original = parse(csvText, { columns: true, skip_empty_lines: true }) as CsvRow[];
	handle = openDb(':memory:');
	report = importCsv(handle.db, csvText);
});

function normalize(value: string | number | null | undefined): string | number | null {
	if (value === null || value === undefined) return null;
	const s = String(value).trim();
	if (s === '') return null;
	const n = Number(s);
	if (Number.isFinite(n) && /^-?[\d.]+(e-?\d+)?$/i.test(s)) return n;
	return s;
}

describe('import of the real CSV', () => {
	it('imports all 61 brews and dedupes to the 10 real bags', () => {
		expect(report.brewsImported).toBe(61);
		expect(report.beansCreated).toBe(10);
	});

	it('keeps the two unnamed legacy brews bean-less instead of inventing a phantom bag', () => {
		const beanless = handle.db.select().from(brews).all().filter((b) => b.beanId === null);
		expect(beanless.map((b) => b.id).sort((a, b) => a - b)).toEqual([26, 27]);
	});

	it('maps every brew to a method and keeps retired/unknown devices out of the registry path', () => {
		const all = handle.db.select().from(brews).all();
		expect(all).toHaveLength(61);
		for (const brew of all) expect(brew.method).toBeTruthy();
		const methods = new Set(all.map((b) => b.method));
		expect(methods.has('french-press')).toBe(false);
		expect(methods.has('espresso')).toBe(false);
	});

	it('preserves legacy brew ids', () => {
		const ids = handle.db
			.select({ id: brews.id })
			.from(brews)
			.all()
			.map((r) => r.id)
			.sort((a, b) => a - b);
		const originalIds = original.map((r) => Number(r.brew_id)).sort((a, b) => a - b);
		expect(ids).toEqual(originalIds);
	});
});

describe('derived fields recompute to the Python pipeline values', () => {
	const derivedCols: { col: CsvColumn; kind: 'number' | 'string'; tolerance?: number }[] = [
		{ col: 'brew_ratio_to_1', kind: 'number' },
		{ col: 'final_extraction_yield_percent', kind: 'number' },
		{ col: 'coffee_grams_per_liter', kind: 'number' },
		{ col: 'score_strength_category', kind: 'string' },
		{ col: 'score_extraction_category', kind: 'string' },
		{ col: 'score_brewing_zone', kind: 'string' },
		{ col: 'score_brew', kind: 'number' },
		{ col: 'score_overall_rating', kind: 'number', tolerance: 0.0005 },
		{ col: 'beans_days_since_roast', kind: 'number' }
	];

	it('matches every stored derived value across all 61 rows', () => {
		const failures: string[] = [];
		for (const row of original) {
			const id = Number(row.brew_id);
			const brew = handle.db.select().from(brews).where(eq(brews.id, id)).get();
			expect(brew, `brew ${id} missing after import`).toBeDefined();
			const bean = brew!.beanId
				? handle.db.select().from(beans).where(eq(beans.id, brew!.beanId)).get()
				: null;
			const derived = deriveBrew(brew!, bean);
			const computed: Record<string, string | number | null> = {
				brew_ratio_to_1: derived.ratio,
				final_extraction_yield_percent: derived.extractionYieldPercent,
				coffee_grams_per_liter: derived.gramsPerLiter,
				score_strength_category: derived.strength,
				score_extraction_category: derived.extraction,
				score_brewing_zone: derived.zone,
				score_brew: derived.brewScore,
				score_overall_rating: derived.overall,
				beans_days_since_roast: derived.daysSinceRoast
			};
			for (const { col, tolerance } of derivedCols) {
				const stored = normalize(row[col]);
				if (stored === null) continue;
				const ours = computed[col];
				if (typeof stored === 'number' && typeof ours === 'number') {
					const ok = tolerance ? Math.abs(stored - ours) <= tolerance : stored === ours;
					if (!ok) failures.push(`brew ${id} ${col}: stored ${stored} ≠ computed ${ours}`);
				} else if (stored !== ours) {
					failures.push(`brew ${id} ${col}: stored ${JSON.stringify(stored)} ≠ computed ${JSON.stringify(ours)}`);
				}
			}
		}
		expect(failures, failures.slice(0, 12).join('\n')).toEqual([]);
	});
});

describe('CSV export round-trips the original', () => {
	it('reproduces every cell value across all 85 columns', () => {
		const exported = parse(exportCsv(handle.db), { columns: true, skip_empty_lines: true }) as CsvRow[];
		expect(exported).toHaveLength(original.length);

		// Bean fields are deduped on import: the canonical value for a bag is the
		// merged first-non-empty across its rows. Compare bean columns against
		// that canonical rather than each raw row.
		const beanCols: CsvColumn[] = [
			'bean_name',
			'bean_origin_country',
			'bean_origin_region',
			'bean_variety',
			'bean_process_method',
			'bean_roast_date',
			'bean_roast_level',
			'bean_notes',
			'bean_purchase_date',
			'estimated_bag_size_grams'
		];
		const canonical = new Map<string, Partial<Record<CsvColumn, string | number | null>>>();
		for (const row of original) {
			const key = `${row.bean_name.trim()}|${row.bean_roast_date.trim()}`;
			const entry = canonical.get(key) ?? {};
			for (const col of beanCols) {
				if (entry[col] === undefined || entry[col] === null) {
					const v = normalize(row[col]);
					if (v !== null) entry[col] = v;
				}
			}
			canonical.set(key, entry);
		}

		// Brew 42 is missing final_brew_mass_grams, so the Python pipeline's
		// all-or-nothing validation never wrote ANY derived field for it — even
		// ratio and strength, which it had the inputs for. Our export computes
		// them; these cells are documented upgrades, not regressions.
		const documentedUpgrades = new Set([
			'42|brew_ratio_to_1',
			'42|score_strength_category',
			'42|coffee_grams_per_liter'
		]);

		const exportedById = new Map(exported.map((r) => [Number(r.brew_id), r]));
		const failures: string[] = [];

		for (const row of original) {
			const id = Number(row.brew_id);
			const out = exportedById.get(id);
			if (!out) {
				failures.push(`brew ${id}: missing from export`);
				continue;
			}
			const key = `${row.bean_name.trim()}|${row.bean_roast_date.trim()}`;
			for (const col of CSV_COLUMNS) {
				if (documentedUpgrades.has(`${id}|${col}`)) continue;
				const expected = beanCols.includes(col)
					? (canonical.get(key)?.[col] ?? null)
					: normalize(row[col]);
				const actual = normalize(out[col]);
				const equal =
					typeof expected === 'number' && typeof actual === 'number'
						? Math.abs(expected - actual) <= 0.0005
						: expected === actual;
				if (!equal) {
					failures.push(`brew ${id} ${col}: original ${JSON.stringify(expected)} → exported ${JSON.stringify(actual)}`);
				}
			}
		}
		expect(failures, `${failures.length} cell diffs\n` + failures.slice(0, 16).join('\n')).toEqual([]);
	});
});
