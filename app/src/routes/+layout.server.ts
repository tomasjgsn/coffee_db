import { count } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { brews } from '$lib/server/db/schema';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = () => {
	const row = getDb().select({ cups: count() }).from(brews).get();
	return { cups: row?.cups ?? 0 };
};
