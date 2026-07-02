import { getDb } from '$lib/server/db/instance';
import { listBrews } from '$lib/server/brew-views';
import { computeMilestones } from '$lib/domain/milestones';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = () => {
	const { items } = listBrews(getDb());

	const drafts = items.filter((i) => i.status === 'draft');

	const today = new Date();
	const isoToday = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
	const todaysCups = items.filter((i) => i.brewedAt === isoToday && i.status === 'complete');

	// Most recent distinct bean+method pairs — one-tap "pour it again".
	const seen = new Set<string>();
	const again: typeof items = [];
	for (const item of items) {
		if (item.status !== 'complete' || item.beanId === null) continue;
		const key = `${item.beanId}|${item.method}`;
		if (seen.has(key)) continue;
		seen.add(key);
		again.push(item);
		if (again.length === 3) break;
	}

	const milestones = computeMilestones(
		items.map((i) => ({
			id: i.id,
			brewedAt: i.brewedAt,
			beanName: i.beanName,
			zone: i.derived.zone,
			overall: i.derived.overall,
			extractionYieldPercent: i.derived.extractionYieldPercent
		}))
	).slice(0, 4);

	return { drafts, todaysCups, again, milestones };
};
