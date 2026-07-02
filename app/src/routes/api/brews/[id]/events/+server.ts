import { error, json } from '@sveltejs/kit';
import { desc, eq } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { brewEvents, brews } from '$lib/server/db/schema';
import { exportDataFiles } from '$lib/server/persist';
import type { RequestHandler } from './$types';

const EVENT_TYPES = new Set([
	'bloom_start',
	'pour_start',
	'pour_end',
	'swirl',
	'stir',
	'valve_open',
	'press_start',
	'press_end',
	'drawdown_end'
]);

function brewOr404(id: string) {
	const brewId = Number(id);
	const db = getDb();
	const brew = db.select().from(brews).where(eq(brews.id, brewId)).get();
	if (!brew) error(404, 'No such brew');
	return { db, brew };
}

export const POST: RequestHandler = async ({ params, request }) => {
	const { db, brew } = brewOr404(params.id);
	const body = (await request.json()) as { elapsedMs?: number; type?: string; waterG?: number | null };

	if (typeof body.elapsedMs !== 'number' || body.elapsedMs < 0) error(400, 'elapsedMs required');
	if (!body.type || !EVENT_TYPES.has(body.type)) error(400, 'unknown event type');

	const event = db
		.insert(brewEvents)
		.values({
			brewId: brew.id,
			elapsedMs: Math.round(body.elapsedMs),
			type: body.type as never,
			waterG: typeof body.waterG === 'number' ? body.waterG : null
		})
		.returning()
		.get();
	exportDataFiles(db);
	return json(event, { status: 201 });
};

export const PATCH: RequestHandler = async ({ params, request }) => {
	const { db, brew } = brewOr404(params.id);
	const body = (await request.json()) as { eventId?: number; waterG?: number | null };
	if (typeof body.eventId !== 'number') error(400, 'eventId required');

	const updated = db
		.update(brewEvents)
		.set({ waterG: typeof body.waterG === 'number' ? body.waterG : null })
		.where(eq(brewEvents.id, body.eventId))
		.returning()
		.get();
	if (!updated || updated.brewId !== brew.id) error(404, 'No such event');
	exportDataFiles(db);
	return json(updated);
};

export const DELETE: RequestHandler = ({ params }) => {
	const { db, brew } = brewOr404(params.id);
	const last = db
		.select()
		.from(brewEvents)
		.where(eq(brewEvents.brewId, brew.id))
		.orderBy(desc(brewEvents.elapsedMs), desc(brewEvents.id))
		.limit(1)
		.get();
	if (!last) return json({ removed: null });
	db.delete(brewEvents).where(eq(brewEvents.id, last.id)).run();
	exportDataFiles(db);
	return json({ removed: last.id });
};
