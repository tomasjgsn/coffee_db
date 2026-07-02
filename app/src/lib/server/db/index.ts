import Database from 'better-sqlite3';
import { drizzle, type BetterSQLite3Database } from 'drizzle-orm/better-sqlite3';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as schema from './schema';

export type Db = BetterSQLite3Database<typeof schema>;

export interface DbHandle {
	db: Db;
	sqlite: Database.Database;
	close: () => void;
}

const here = dirname(fileURLToPath(import.meta.url));
const MIGRATIONS_DIR = join(here, 'migrations');

/** Repo-relative default: data/coffee.db next to the legacy CSV. */
export const DEFAULT_DB_PATH =
	process.env.COFFEE_DB_PATH ?? join(here, '..', '..', '..', '..', '..', 'data', 'coffee.db');

/**
 * Open (or create) a database and bring it up to date. Pass ':memory:' in
 * tests — never point tests at the real data file.
 */
export function openDb(path: string = DEFAULT_DB_PATH): DbHandle {
	const sqlite = new Database(path);
	sqlite.pragma('journal_mode = WAL');
	sqlite.pragma('foreign_keys = ON');
	applyMigrations(sqlite);
	const db = drizzle(sqlite, { schema });
	return { db, sqlite, close: () => sqlite.close() };
}

function applyMigrations(sqlite: Database.Database): void {
	sqlite.exec(
		'CREATE TABLE IF NOT EXISTS __migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)'
	);
	const applied = new Set(
		(sqlite.prepare('SELECT name FROM __migrations').all() as { name: string }[]).map((r) => r.name)
	);
	const files = readdirSync(MIGRATIONS_DIR)
		.filter((f) => f.endsWith('.sql'))
		.sort();
	const record = sqlite.prepare('INSERT INTO __migrations (name, applied_at) VALUES (?, ?)');
	for (const file of files) {
		if (applied.has(file)) continue;
		const sql = readFileSync(join(MIGRATIONS_DIR, file), 'utf-8');
		sqlite.transaction(() => {
			sqlite.exec(sql);
			record.run(file, new Date().toISOString());
		})();
	}
}
