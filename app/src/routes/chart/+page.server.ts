import { getDb } from '$lib/server/db/instance';
import { listBrews } from '$lib/server/brew-views';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = () => {
	const { items } = listBrews(getDb());

	// Chronological, only cups with a full reading.
	const measured = items
		.filter(
			(i) =>
				i.derived.extractionYieldPercent !== null &&
				i.tdsPercent !== null &&
				i.status === 'complete'
		)
		.reverse();

	const points = measured.map((i, idx) => ({
		id: i.id,
		ey: i.derived.extractionYieldPercent!,
		tds: i.tdsPercent!,
		score: i.derived.overall,
		label: `Nº${i.id} · ${i.beanName ?? 'unnamed'} · ${i.brewedAt} · ${i.derived.extractionYieldPercent}% · ${i.derived.zone ?? ''}`,
		latest: idx === measured.length - 1,
		beanName: i.beanName,
		brewedAt: i.brewedAt,
		zone: i.derived.zone
	}));

	const last10 = points.slice(-10);
	const prev10 = points.slice(-20, -10);
	const hitRate = (slice: typeof points) =>
		slice.length === 0
			? null
			: Math.round((slice.filter((p) => p.zone === 'Ideal-Ideal').length / slice.length) * 100);

	const scored = measured.filter((i) => i.derived.overall !== null);

	return {
		points,
		hitRateNow: hitRate(last10),
		hitRateBefore: hitRate(prev10),
		avgScoreNow: avg(last10.map((p) => p.score)),
		trend: scored.map((i) => ({ id: i.id, at: i.brewedAt, score: i.derived.overall! })),
		beans: [...new Set(points.map((p) => p.beanName).filter((b): b is string => !!b))]
	};
};

function avg(values: (number | null)[]): number | null {
	const nums = values.filter((v): v is number => v !== null);
	if (nums.length === 0) return null;
	return Math.round((nums.reduce((s, v) => s + v, 0) / nums.length) * 10) / 10;
}
