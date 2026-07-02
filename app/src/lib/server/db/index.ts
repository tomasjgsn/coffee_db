import Database from 'better-sqlite3';
import { drizzle, type BetterSQLite3Database } from 'drizzle-orm/better-sqlite3';
import { join } from 'node:path';
import { MIGRATIONS } from './migrations';
import * as schema from './schema';

export type Db = BetterSQLite3Database<typeof schema>;

export interface DbHandle {
	db: Db;
	sqlite: Database.Database;
	close: () => void;
}

/**
 * Repo-relative default: data/coffee.db next to the legacy CSV. The dev
 * server, preview server, and scripts all run with app/ as the working
 * directory, so resolve from there (import.meta.url is unreliable once
 * adapter-node has bundled this module).
 */
export function defaultDbPath(): string {
	return process.env.COFFEE_DB_PATH ?? join(process.cwd(), '..', 'data', 'coffee.db');
}

/**
 * Open (or create) a database and bring it up to date. Pass ':memory:' in
 * tests — never point tests at the real data file.
 */
export function openDb(path: string = defaultDbPath()): DbHandle {
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
	const record = sqlite.prepare('INSERT INTO __migrations (name, applied_at) VALUES (?, ?)');
	for (const migration of MIGRATIONS) {
		if (applied.has(migration.name)) continue;
		sqlite.transaction(() => {
			sqlite.exec(migration.sql);
			record.run(migration.name, new Date().toISOString());
		})();
	}
}
