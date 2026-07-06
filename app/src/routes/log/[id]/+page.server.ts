import { error, fail, redirect } from '@sveltejs/kit';
import { asc, eq } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { beans, brewEvents, brews } from '$lib/server/db/schema';
import { deriveBrew } from '$lib/brewing/derive';
import { exportDataFiles } from '$lib/server/persist';
import { PICKABLE_METHOD_IDS } from '$lib/server/prefill';
import { parseClock } from '$lib/format';
import type { Actions, PageServerLoad } from './$types';

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

export const actions: Actions = {
	update: async ({ params, request }) => {
		const db = getDb();
		const id = Number(params.id);
		const brew = db.select().from(brews).where(eq(brews.id, id)).get();
		if (!brew) error(404, 'No such cup');

		const form = await request.formData();
		const optional = (name: string): number | null => {
			const raw = String(form.get(name) ?? '').trim();
			if (raw === '') return null;
			const value = Number(raw);
			return Number.isFinite(value) ? value : null;
		};
		const text = (name: string): string | null => String(form.get(name) ?? '').trim() || null;

		const method = String(form.get('method') ?? brew.method);
		if (method !== brew.method && !PICKABLE_METHOD_IDS.has(method as never)) {
			return fail(400, { message: 'Unknown method' });
		}

		let totalTimeS = brew.totalTimeS;
		const typedTime = String(form.get('totalTime') ?? '').trim();
		if (typedTime !== '') {
			const parsed = parseClock(typedTime);
			if (parsed === null) return fail(400, { message: 'Time format: 3:02' });
			totalTimeS = parsed;
		} else {
			totalTimeS = null;
		}

		db.update(brews)
			.set({
				method,
				doseG: optional('doseG'),
				waterG: optional('waterG'),
				tempC: optional('tempC'),
				grindSize: optional('grindSize'),
				mugWeightG: optional('mugWeightG'),
				finalCombinedWeightG: optional('finalCombinedWeightG'),
				brewMassG: optional('brewMassG'),
				tdsPercent: optional('tdsPercent'),
				totalTimeS,
				scoreComplexity: optional('scoreComplexity'),
				scoreBitterness: optional('scoreBitterness'),
				scoreMouthfeel: optional('scoreMouthfeel'),
				tastingNotes: text('tastingNotes'),
				notes: text('notes'),
				updatedAt: new Date().toISOString()
			})
			.where(eq(brews.id, id))
			.run();
		exportDataFiles(db);
		return { updated: true };
	},
	remove: ({ params }) => {
		const db = getDb();
		const id = Number(params.id);
		db.delete(brews).where(eq(brews.id, id)).run();
		exportDataFiles(db);
		redirect(303, '/log');
	}
};
