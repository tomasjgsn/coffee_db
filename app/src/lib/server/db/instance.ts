import { openDb, type Db, type DbHandle } from './index';

let handle: DbHandle | null = null;

/** Process-wide database handle for the running app. Tests use openDb(':memory:') instead. */
export function getDb(): Db {
	if (!handle) handle = openDb();
	return handle.db;
}
