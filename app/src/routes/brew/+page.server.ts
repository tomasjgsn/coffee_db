import { fail, redirect } from '@sveltejs/kit';
import { desc, eq } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { beans, brews } from '$lib/server/db/schema';
import { shelf } from '$lib/server/brew-views';
import { prefillFor, PICKABLE_METHOD_IDS } from '$lib/server/prefill';
import { METHODS, type MethodId } from '$lib/domain/methods';
import { exportDataFiles } from '$lib/server/persist';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = ({ url }) => {
	const db = getDb();
	const bags = shelf(db).filter((item) => !item.bean.archived);

	const beanParam = Number(url.searchParams.get('bean'));
	const methodParam = url.searchParams.get('method');
	const initialBeanId = bags.some((b) => b.bean.id === beanParam) ? beanParam : null;
	const initialMethod = PICKABLE_METHOD_IDS.has(methodParam as MethodId)
		? (methodParam as MethodId)
		: null;

	const prefills: Record<number, Partial<Record<MethodId, ReturnType<typeof prefillFor>>>> = {};
	const lastMethod: Record<number, MethodId> = {};
	for (const bag of bags) {
		prefills[bag.bean.id] = {};
		for (const method of METHODS) {
			prefills[bag.bean.id][method.id] = prefillFor(db, bag.bean.id, method.id);
		}
		const latest = db
			.select({ method: brews.method })
			.from(brews)
			.where(eq(brews.beanId, bag.bean.id))
			.orderBy(desc(brews.brewedAt), desc(brews.id))
			.limit(1)
			.get();
		if (latest && PICKABLE_METHOD_IDS.has(latest.method as MethodId)) {
			lastMethod[bag.bean.id] = latest.method as MethodId;
		}
	}

	return { bags, prefills, lastMethod, initialBeanId, initialMethod };
};

export const actions: Actions = {
	start: async ({ request }) => {
		const form = await request.formData();
		const db = getDb();

		const beanId = Number(form.get('beanId'));
		const method = String(form.get('method'));
		const doseG = Number(form.get('doseG'));
		const waterG = Number(form.get('waterG'));

		if (!Number.isInteger(beanId) || !db.select().from(beans).where(eq(beans.id, beanId)).get()) {
			return fail(400, { message: 'Pick a bag first' });
		}
		if (!PICKABLE_METHOD_IDS.has(method as MethodId)) {
			return fail(400, { message: 'Pick a brewer' });
		}
		if (!(doseG > 0) || !(waterG > 0)) {
			return fail(400, { message: 'Dose and water must be above zero' });
		}

		const optional = (name: string): number | null => {
			const raw = String(form.get(name) ?? '').trim();
			if (raw === '') return null;
			const value = Number(raw);
			return Number.isFinite(value) ? value : null;
		};

		let plan: unknown = null;
		try {
			plan = JSON.parse(String(form.get('plan') ?? 'null'));
		} catch {
			plan = null;
		}

		const now = new Date();
		const isoDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

		const inserted = getDb()
			.insert(brews)
			.values({
				beanId,
				brewedAt: isoDate,
				method,
				status: 'draft',
				doseG,
				waterG,
				tempC: optional('tempC'),
				grindSize: optional('grindSize'),
				grinder: String(form.get('grinder') ?? '').trim() || null,
				iceG: optional('iceG'),
				hotWaterG: optional('hotWaterG'),
				mugWeightG: optional('mugWeightG'),
				methodParams: plan ? JSON.stringify({ plan }) : null,
				createdAt: now.toISOString(),
				updatedAt: now.toISOString()
			})
			.returning({ id: brews.id })
			.get();

		exportDataFiles(db);
		redirect(303, `/brew/${inserted.id}/live`);
	}
};
