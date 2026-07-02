/**
 * One-shot migration: data/cups_of_coffee.csv → data/coffee.db.
 * Usage: npm run db:import [-- --force]
 * --force deletes an existing database first; without it the script refuses
 * to touch a database that already has brews.
 */
import { readFileSync, existsSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { openDb } from '../src/lib/server/db';
import { brews } from '../src/lib/server/db/schema';
import { importCsv } from '../src/lib/server/import/csv-import';
import { exportCsv } from '../src/lib/server/export/csv-export';

const here = dirname(fileURLToPath(import.meta.url));
const dataDir = join(here, '..', '..', 'data');
const csvPath = process.env.COFFEE_CSV_PATH ?? join(dataDir, 'cups_of_coffee.csv');
const dbPath = process.env.COFFEE_DB_PATH ?? join(dataDir, 'coffee.db');
const force = process.argv.includes('--force');

if (existsSync(dbPath) && force) {
	rmSync(dbPath);
	for (const suffix of ['-wal', '-shm']) {
		if (existsSync(dbPath + suffix)) rmSync(dbPath + suffix);
	}
	console.log(`Removed existing ${dbPath}`);
}

const handle = openDb(dbPath);
const existing = handle.db.select({ id: brews.id }).from(brews).all();
if (existing.length > 0) {
	console.error(`${dbPath} already holds ${existing.length} brews. Re-run with --force to rebuild.`);
	handle.close();
	process.exit(1);
}

const csvText = readFileSync(csvPath, 'utf-8');
const report = importCsv(handle.db, csvText);

console.log(`Imported ${report.brewsImported} brews across ${report.beansCreated} beans from ${csvPath}`);
for (const warning of report.warnings) console.log(`  note: ${warning}`);

const exportedRows = exportCsv(handle.db).trim().split('\n').length - 1;
console.log(`Export check: ${exportedRows} rows reproducible from the database.`);
handle.close();
