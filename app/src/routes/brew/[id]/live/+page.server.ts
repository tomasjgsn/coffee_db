import { error, redirect } from '@sveltejs/kit';
import { asc, eq } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { beans, brewEvents, brews } from '$lib/server/db/schema';
import { exportDataFiles } from '$lib/server/persist';
import type { PourPlan } from '$lib/domain/templates';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = ({ params }) => {
	const db = getDb();
	const brew = db.select().from(brews).where(eq(brews.id, Number(params.id))).get();
	if (!brew) error(404, 'No such brew');

	const bean = brew.beanId !== null
		? (db.select().from(beans).where(eq(beans.id, brew.beanId)).get() ?? null)
		: null;
	const events = db
		.select()
		.from(brewEvents)
		.where(eq(brewEvents.brewId, brew.id))
		.orderBy(asc(brewEvents.elapsedMs), asc(brewEvents.id))
		.all();

	let plan: PourPlan | null = null;
	if (brew.methodParams) {
		try {
			plan = (JSON.parse(brew.methodParams) as { plan?: PourPlan }).plan ?? null;
		} catch {
			plan = null;
		}
	}

	return { brew, bean, events, plan };
};

export const actions: Actions = {
	finish: ({ params }) => {
		const db = getDb();
		const id = Number(params.id);
		const brew = db.select().from(brews).where(eq(brews.id, id)).get();
		if (!brew) error(404, 'No such brew');

		const events = db
			.select()
			.from(brewEvents)
			.where(eq(brewEvents.brewId, id))
			.orderBy(asc(brewEvents.elapsedMs))
			.all();

		const drawdown = events.filter((e) => e.type === 'drawdown_end').at(-1);
		let totalTimeS = brew.totalTimeS;
		if (drawdown) {
			totalTimeS = Math.round(drawdown.elapsedMs / 100) / 10;
		} else if (brew.startedAt) {
			totalTimeS = Math.round((Date.now() - Date.parse(brew.startedAt)) / 100) / 10;
		}

		db.update(brews)
			.set({ totalTimeS, updatedAt: new Date().toISOString() })
			.where(eq(brews.id, id))
			.run();
		exportDataFiles(db);
		redirect(303, `/brew/${id}/taste`);
	}
};
