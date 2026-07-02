import { error, fail, redirect } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { beans, brews } from '$lib/server/db/schema';
import { exportDataFiles } from '$lib/server/persist';
import { parseClock } from '$lib/format';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = ({ params, url }) => {
	const db = getDb();
	const brew = db.select().from(brews).where(eq(brews.id, Number(params.id))).get();
	if (!brew) error(404, 'No such brew');
	const bean = brew.beanId !== null
		? (db.select().from(beans).where(eq(beans.id, brew.beanId)).get() ?? null)
		: null;
	return { brew, bean, manual: url.searchParams.get('manual') === '1' };
};

export const actions: Actions = {
	save: async ({ params, request }) => {
		const db = getDb();
		const id = Number(params.id);
		const brew = db.select().from(brews).where(eq(brews.id, id)).get();
		if (!brew) error(404, 'No such brew');

		const form = await request.formData();
		const intent = String(form.get('intent') ?? 'draft');

		const optional = (name: string): number | null => {
			const raw = String(form.get(name) ?? '').trim();
			if (raw === '') return null;
			const value = Number(raw);
			return Number.isFinite(value) ? value : null;
		};
		const text = (name: string): string | null => String(form.get(name) ?? '').trim() || null;

		const mugWeightG = optional('mugWeightG');
		const finalCombinedWeightG = optional('finalCombinedWeightG');
		let brewMassG = optional('brewMassG');
		if (brewMassG === null && mugWeightG !== null && finalCombinedWeightG !== null) {
			brewMassG = Math.round((finalCombinedWeightG - mugWeightG) * 10) / 10;
		}
		if (brewMassG !== null && brewMassG < 0) {
			return fail(400, { message: 'Combined weight is lighter than the mug — check the scale' });
		}

		let totalTimeS = brew.totalTimeS;
		const typedTime = String(form.get('totalTime') ?? '').trim();
		if (typedTime !== '') {
			const parsed = parseClock(typedTime);
			if (parsed === null) return fail(400, { message: 'Total time reads like 3:02' });
			totalTimeS = parsed;
		}

		db.update(brews)
			.set({
				tdsPercent: optional('tdsPercent'),
				mugWeightG,
				finalCombinedWeightG,
				brewMassG,
				totalTimeS,
				scoreComplexity: optional('scoreComplexity'),
				scoreBitterness: optional('scoreBitterness'),
				scoreMouthfeel: optional('scoreMouthfeel'),
				flavorProfile: text('flavorProfile'),
				tastingNotes: text('tastingNotes'),
				notes: text('notes'),
				status: intent === 'complete' ? 'complete' : 'draft',
				updatedAt: new Date().toISOString()
			})
			.where(eq(brews.id, id))
			.run();

		exportDataFiles(db);
		redirect(303, intent === 'complete' ? `/log/${id}?stamped=1` : `/`);
	}
};
