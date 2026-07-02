/** Milestones — stamps earned by brewing. Pure and testable. */

export interface MilestoneBrew {
	id: number;
	brewedAt: string;
	beanName: string | null;
	zone: string | null;
	overall: number | null;
	extractionYieldPercent: number | null;
}

export interface Milestone {
	kind: 'count' | 'dialed-in' | 'best' | 'streak';
	label: string;
	sub: string;
	earnedAt: string;
	brewId: number | null;
}

const COUNT_MARKS = [10, 25, 50, 100, 150, 200, 250, 365, 500, 1000];

export function computeMilestones(brews: MilestoneBrew[]): Milestone[] {
	const ordered = [...brews].sort((a, b) => a.brewedAt.localeCompare(b.brewedAt) || a.id - b.id);
	const milestones: Milestone[] = [];

	for (const mark of COUNT_MARKS) {
		if (ordered.length >= mark) {
			const cup = ordered[mark - 1];
			milestones.push({
				kind: 'count',
				label: `Cup Nº${mark}`,
				sub: `poured ${cup.brewedAt}`,
				earnedAt: cup.brewedAt,
				brewId: cup.id
			});
		}
	}

	const dialedIn = new Set<string>();
	for (const brew of ordered) {
		if (brew.zone === 'Ideal-Ideal' && brew.beanName && !dialedIn.has(brew.beanName)) {
			dialedIn.add(brew.beanName);
			milestones.push({
				kind: 'dialed-in',
				label: `${brew.beanName}, dialed in`,
				sub: 'first Ideal-Ideal on this bag',
				earnedAt: brew.brewedAt,
				brewId: brew.id
			});
		}
	}

	let best: MilestoneBrew | null = null;
	for (const brew of ordered) {
		if (brew.overall !== null && (best === null || brew.overall > best.overall!)) best = brew;
	}
	if (best?.overall != null) {
		milestones.push({
			kind: 'best',
			label: `Personal best ${best.overall.toFixed(1)}`,
			sub: `${best.beanName ?? 'unnamed cup'} · ${best.brewedAt}`,
			earnedAt: best.brewedAt,
			brewId: best.id
		});
	}

	let run = 0;
	let bestRun = 0;
	let bestRunEnd: MilestoneBrew | null = null;
	for (const brew of ordered) {
		if (brew.zone === null) continue;
		if (brew.zone === 'Ideal-Ideal') {
			run += 1;
			if (run > bestRun) {
				bestRun = run;
				bestRunEnd = brew;
			}
		} else {
			run = 0;
		}
	}
	if (bestRun >= 3 && bestRunEnd) {
		milestones.push({
			kind: 'streak',
			label: `${bestRun} ideal cups running`,
			sub: `ended ${bestRunEnd.brewedAt}`,
			earnedAt: bestRunEnd.brewedAt,
			brewId: bestRunEnd.id
		});
	}

	return milestones.sort((a, b) => b.earnedAt.localeCompare(a.earnedAt));
}
