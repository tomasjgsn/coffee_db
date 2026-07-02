import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { asc } from 'drizzle-orm';
import { stringify } from 'csv-stringify/sync';
import type { Db } from '$lib/server/db';
import { brewEvents } from '$lib/server/db/schema';
import { exportCsv } from '$lib/server/export/csv-export';

function dataDir(): string {
	return process.env.COFFEE_DATA_DIR ?? join(process.cwd(), '..', 'data');
}

/**
 * Write the git-diffable records after any mutation: the legacy-compatible
 * 85-column brews CSV, plus the event timeline CSV (new-world data with no
 * legacy columns of its own).
 */
export function exportDataFiles(db: Db): void {
	writeFileSync(join(dataDir(), 'cups_of_coffee.csv'), exportCsv(db));

	const events = db.select().from(brewEvents).orderBy(asc(brewEvents.brewId), asc(brewEvents.elapsedMs)).all();
	const eventsCsv = stringify(events, {
		header: true,
		columns: ['id', 'brewId', 'elapsedMs', 'type', 'waterG', 'note']
	});
	writeFileSync(join(dataDir(), 'brew_events.csv'), eventsCsv);
}
