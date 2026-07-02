/**
 * Build a disposable database + data dir for e2e runs so tests never touch
 * data/coffee.db or data/cups_of_coffee.csv. Seeded from the real CSV
 * (read-only) on every run.
 */
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { openDb } from '../src/lib/server/db';
import { importCsv } from '../src/lib/server/import/csv-import';

const here = dirname(fileURLToPath(import.meta.url));
const appDir = join(here, '..');
const sourceCsv = join(appDir, '..', 'data', 'cups_of_coffee.csv');
const e2eDir = join(appDir, '.e2e-data');

if (existsSync(e2eDir)) rmSync(e2eDir, { recursive: true });
mkdirSync(e2eDir);

copyFileSync(sourceCsv, join(e2eDir, 'cups_of_coffee.csv'));

const handle = openDb(join(e2eDir, 'coffee.db'));
const report = importCsv(handle.db, readFileSync(sourceCsv, 'utf-8'));
handle.close();

console.log(`e2e sandbox ready: ${report.brewsImported} brews, ${report.beansCreated} beans in ${e2eDir}`);
