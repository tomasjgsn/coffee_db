import { describe, expect, it } from 'vitest';
import { computeMilestones, type MilestoneBrew } from '$lib/domain/milestones';

function brew(partial: Partial<MilestoneBrew> & { id: number }): MilestoneBrew {
	return {
		brewedAt: '2026-01-01',
		beanName: 'Test Bag',
		zone: null,
		overall: null,
		extractionYieldPercent: null,
		...partial
	};
}

describe('milestones', () => {
	it('awards cup-count milestones at 10, 25, 50, 100', () => {
		const brews = Array.from({ length: 26 }, (_, i) => brew({ id: i + 1 }));
		const milestones = computeMilestones(brews);
		const counts = milestones.filter((m) => m.kind === 'count').map((m) => m.label);
		expect(counts).toContain('Cup Nº10');
		expect(counts).toContain('Cup Nº25');
		expect(counts).not.toContain('Cup Nº50');
	});

	it('awards the first Ideal-Ideal per bean, once', () => {
		const brews = [
			brew({ id: 1, beanName: 'Hamararo', zone: 'Under-Weak' }),
			brew({ id: 2, beanName: 'Hamararo', zone: 'Ideal-Ideal', brewedAt: '2026-01-02' }),
			brew({ id: 3, beanName: 'Hamararo', zone: 'Ideal-Ideal', brewedAt: '2026-01-03' }),
			brew({ id: 4, beanName: 'La Palma', zone: 'Ideal-Ideal', brewedAt: '2026-01-04' })
		];
		const dialedIn = computeMilestones(brews).filter((m) => m.kind === 'dialed-in');
		expect(dialedIn).toHaveLength(2);
		const hamararo = dialedIn.find((m) => m.label.includes('Hamararo'));
		expect(hamararo?.brewId).toBe(2);
	});

	it('tracks the personal best overall score as it improves', () => {
		const brews = [
			brew({ id: 1, overall: 3.5 }),
			brew({ id: 2, overall: 4.2, brewedAt: '2026-01-02' }),
			brew({ id: 3, overall: 4.0, brewedAt: '2026-01-03' })
		];
		const best = computeMilestones(brews).filter((m) => m.kind === 'best');
		expect(best).toHaveLength(1);
		expect(best[0].brewId).toBe(2);
		expect(best[0].label).toContain('4.2');
	});

	it('reports the longest ideal-zone streak of three or more', () => {
		const zones = ['Ideal-Ideal', 'Ideal-Ideal', 'Ideal-Ideal', 'Under-Weak', 'Ideal-Ideal'];
		const brews = zones.map((zone, i) => brew({ id: i + 1, zone, brewedAt: `2026-01-0${i + 1}` }));
		const streaks = computeMilestones(brews).filter((m) => m.kind === 'streak');
		expect(streaks).toHaveLength(1);
		expect(streaks[0].label).toContain('3');
	});

	it('returns newest milestones first', () => {
		const brews = [
			brew({ id: 1, zone: 'Ideal-Ideal', brewedAt: '2025-06-01', beanName: 'Old Bag' }),
			...Array.from({ length: 10 }, (_, i) =>
				brew({ id: i + 2, brewedAt: `2026-01-${String(i + 1).padStart(2, '0')}` })
			)
		];
		const milestones = computeMilestones(brews);
		expect(milestones[0].earnedAt >= milestones.at(-1)!.earnedAt).toBe(true);
	});
});
