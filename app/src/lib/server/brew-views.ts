import { desc } from 'drizzle-orm';
import type { Db } from '$lib/server/db';
import { beans, brews, type Bean, type Brew } from '$lib/server/db/schema';
import { deriveBrew, type DerivedBrew } from '$lib/brewing/derive';

export interface BrewListItem {
	id: number;
	brewedAt: string;
	method: string;
	status: string;
	beanName: string | null;
	beanId: number | null;
	derived: DerivedBrew;
}

export interface BeanShelfItem {
	bean: Bean;
	brewCount: number;
	bestScore: number | null;
	avgOverall: number | null;
	lastBrewedAt: string | null;
	dosedGrams: number;
}

export function listBrews(db: Db): { items: BrewListItem[]; beansById: Map<number, Bean> } {
	const allBeans = db.select().from(beans).all();
	const beansById = new Map(allBeans.map((b) => [b.id, b]));
	const rows = db.select().from(brews).orderBy(desc(brews.brewedAt), desc(brews.id)).all();
	const items = rows.map((brew) => toListItem(brew, beansById));
	return { items, beansById };
}

function toListItem(brew: Brew, beansById: Map<number, Bean>): BrewListItem {
	const bean = brew.beanId !== null ? (beansById.get(brew.beanId) ?? null) : null;
	return {
		id: brew.id,
		brewedAt: brew.brewedAt,
		method: brew.method,
		status: brew.status,
		beanName: bean?.name ?? null,
		beanId: bean?.id ?? null,
		derived: deriveBrew(brew, bean)
	};
}

export function shelf(db: Db): BeanShelfItem[] {
	const allBeans = db.select().from(beans).all();
	const allBrews = db.select().from(brews).all();

	return allBeans
		.map((bean) => {
			const own = allBrews.filter((b) => b.beanId === bean.id);
			const overalls = own
				.map((b) => deriveBrew(b, bean).overall)
				.filter((v): v is number => v !== null);
			const dosed = own.reduce((sum, b) => sum + (b.doseG ?? 0), 0);
			const last = own.map((b) => b.brewedAt).sort().at(-1) ?? null;
			return {
				bean,
				brewCount: own.length,
				bestScore: overalls.length > 0 ? Math.max(...overalls) : null,
				avgOverall:
					overalls.length > 0
						? Math.round((overalls.reduce((s, v) => s + v, 0) / overalls.length) * 10) / 10
						: null,
				lastBrewedAt: last,
				dosedGrams: Math.round(dosed * 10) / 10
			};
		})
		.sort((a, b) => (b.lastBrewedAt ?? '').localeCompare(a.lastBrewedAt ?? ''));
}
