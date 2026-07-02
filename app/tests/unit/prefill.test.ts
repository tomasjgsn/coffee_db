import { beforeAll, describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { eq } from 'drizzle-orm';
import { openDb, type DbHandle } from '$lib/server/db';
import { beans } from '$lib/server/db/schema';
import { importCsv } from '$lib/server/import/csv-import';
import { prefillFor } from '$lib/server/prefill';

const CSV_PATH = join(
	dirname(fileURLToPath(import.meta.url)),
	'..', '..', '..', 'data', 'cups_of_coffee.csv'
);

let handle: DbHandle;
let raroBodaId: number;

beforeAll(() => {
	handle = openDb(':memory:');
	importCsv(handle.db, readFileSync(CSV_PATH, 'utf-8'));
	raroBodaId = handle.db.select().from(beans).where(eq(beans.name, 'Raro Boda')).get()!.id;
});

describe('recipe prefill', () => {
	it('uses the last brew of the same bean and method as the starting recipe', () => {
		const prefill = prefillFor(handle.db, raroBodaId, 'hario-switch');
		expect(prefill.source.kind).toBe('same-method');
		expect(prefill.doseG).toBe(16.2);
		expect(prefill.waterG).toBe(250);
	});

	it('falls back to the same bean on another method', () => {
		const prefill = prefillFor(handle.db, raroBodaId, 'aeropress');
		expect(prefill.source.kind).toBe('same-bean');
		expect(prefill.doseG).toBeGreaterThan(0);
	});

	it('falls back to the method template for a fresh combination with no history', () => {
		const fresh = handle.db
			.insert(beans)
			.values({ name: 'Brand New Bag', createdAt: 'x', updatedAt: 'x', archived: false })
			.returning({ id: beans.id })
			.get();
		const prefill = prefillFor(handle.db, fresh.id, 'v60');
		expect(prefill.source.kind).toBe('template');
		expect(prefill.plan.pours.at(-1)!.targetG).toBe(prefill.waterG);
	});
});
