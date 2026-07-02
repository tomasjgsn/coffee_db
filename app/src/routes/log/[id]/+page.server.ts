import { error } from '@sveltejs/kit';
import { asc, eq } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { beans, brewEvents, brews } from '$lib/server/db/schema';
import { deriveBrew } from '$lib/brewing/derive';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = ({ params }) => {
	const id = Number(params.id);
	if (!Number.isInteger(id)) error(404, 'No such cup');

	const db = getDb();
	const brew = db.select().from(brews).where(eq(brews.id, id)).get();
	if (!brew) error(404, 'No such cup');

	const bean = brew.beanId !== null
		? (db.select().from(beans).where(eq(beans.id, brew.beanId)).get() ?? null)
		: null;
	const events = db
		.select()
		.from(brewEvents)
		.where(eq(brewEvents.brewId, id))
		.orderBy(asc(brewEvents.elapsedMs))
		.all();

	return {
		brew,
		bean,
		events,
		derived: deriveBrew(brew, bean),
		methodParams: brew.methodParams ? (JSON.parse(brew.methodParams) as Record<string, string | number>) : {}
	};
};
