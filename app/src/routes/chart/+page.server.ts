import { getDb } from '$lib/server/db/instance';
import { listBrews } from '$lib/server/brew-views';
import type { PageServerLoad } from './$types';

export interface ChartPointData {
	id: number;
	ey: number;
	tds: number;
	overall: number | null;
	brewScore: number | null;
	zone: string | null;
	beanName: string | null;
	brewedAt: string;
	method: string;
	grindSize: number | null;
	tempC: number | null;
	ratio: number | null;
	restDays: number | null;
	flavorProfile: string | null;
	tastingNotes: string | null;
}

/**
 * One rich chronological payload; every filter, stat, and panel derives from
 * it client-side (the whole history is ~60 cups).
 */
export const load: PageServerLoad = () => {
	const { items } = listBrews(getDb());

	const points: ChartPointData[] = items
		.filter(
			(i) =>
				i.status === 'complete' &&
				i.derived.extractionYieldPercent !== null &&
				i.tdsPercent !== null
		)
		.reverse()
		.map((i) => ({
			id: i.id,
			ey: i.derived.extractionYieldPercent!,
			tds: i.tdsPercent!,
			overall: i.derived.overall,
			brewScore: i.derived.brewScore,
			zone: i.derived.zone,
			beanName: i.beanName,
			brewedAt: i.brewedAt,
			method: i.method,
			grindSize: i.grindSize,
			tempC: i.tempC,
			ratio: i.derived.ratio,
			restDays: i.restDays,
			flavorProfile: i.flavorProfile,
			tastingNotes: i.tastingNotes
		}));

	return { points };
};
