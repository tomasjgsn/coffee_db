import { error, json } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { brews } from '$lib/server/db/schema';
import { exportDataFiles } from '$lib/server/persist';
import type { RequestHandler } from './$types';

/** Idempotent: sets started_at once; a reload never resets the clock. */
export const POST: RequestHandler = ({ params }) => {
	const db = getDb();
	const brew = db.select().from(brews).where(eq(brews.id, Number(params.id))).get();
	if (!brew) error(404, 'No such brew');

	if (brew.startedAt) return json({ startedAt: brew.startedAt });

	const startedAt = new Date().toISOString();
	db.update(brews)
		.set({ startedAt, updatedAt: startedAt })
		.where(eq(brews.id, brew.id))
		.run();
	exportDataFiles(db);
	return json({ startedAt });
};
