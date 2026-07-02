import { fail } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';
import { getDb } from '$lib/server/db/instance';
import { beans } from '$lib/server/db/schema';
import { shelf } from '$lib/server/brew-views';
import { exportDataFiles } from '$lib/server/persist';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = () => {
	return { shelf: shelf(getDb()) };
};

export const actions: Actions = {
	add: async ({ request }) => {
		const db = getDb();
		const form = await request.formData();
		const text = (name: string): string | null => String(form.get(name) ?? '').trim() || null;
		const name = text('name');
		if (!name) return fail(400, { message: 'A bag needs a name' });

		const bagSizeRaw = String(form.get('bagSizeG') ?? '').trim();
		const bagSizeG = bagSizeRaw === '' ? null : Number(bagSizeRaw);
		if (bagSizeG !== null && !(bagSizeG > 0)) return fail(400, { message: 'Bag size in grams' });

		const now = new Date().toISOString();
		db.insert(beans)
			.values({
				name,
				originCountry: text('originCountry'),
				originRegion: text('originRegion'),
				variety: text('variety'),
				process: text('process'),
				roastLevel: text('roastLevel'),
				roastDate: text('roastDate'),
				purchaseDate: text('purchaseDate'),
				bagSizeG,
				notes: text('notes'),
				archived: false,
				createdAt: now,
				updatedAt: now
			})
			.run();
		exportDataFiles(db);
		return { added: name };
	},
	archive: async ({ request }) => {
		const db = getDb();
		const form = await request.formData();
		const id = Number(form.get('beanId'));
		const bean = db.select().from(beans).where(eq(beans.id, id)).get();
		if (!bean) return fail(404, { message: 'No such bag' });
		db.update(beans)
			.set({ archived: !bean.archived, updatedAt: new Date().toISOString() })
			.where(eq(beans.id, id))
			.run();
		exportDataFiles(db);
		return { archived: !bean.archived };
	}
};
