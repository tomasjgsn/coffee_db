import { describe, expect, it } from 'vitest';
import { templateFor } from './templates';
import { METHODS } from './methods';

describe('method recipe templates', () => {
	it('provides a sane starting recipe for every pickable method', () => {
		for (const method of METHODS) {
			const t = templateFor(method.id);
			expect(t.doseG).toBeGreaterThan(0);
			expect(t.waterG).toBeGreaterThan(t.doseG);
			expect(t.tempC).toBeGreaterThanOrEqual(70);
			expect(t.tempC).toBeLessThanOrEqual(100);
		}
	});

	it('builds ascending pour plans that end at the poured water weight', () => {
		for (const method of METHODS) {
			const t = templateFor(method.id);
			if (t.plan.pours.length === 0) continue;
			let lastAt = -1;
			let lastTarget = 0;
			for (const pour of t.plan.pours) {
				expect(pour.at).toBeGreaterThan(lastAt);
				expect(pour.targetG).toBeGreaterThanOrEqual(lastTarget);
				lastAt = pour.at;
				lastTarget = pour.targetG;
			}
			// Iced methods pour only the hot fraction — the ice is already in the vessel.
			const pouredTarget = method.iced ? t.hotWaterG : t.waterG;
			expect(t.plan.pours.at(-1)!.targetG).toBe(pouredTarget);
		}
	});

	it('splits iced aeropress water into hot water and ice totalling the water weight', () => {
		const t = templateFor('aeropress-iced');
		expect(t.iceG).toBeGreaterThan(0);
		expect(t.hotWaterG).toBeGreaterThan(0);
		expect(t.iceG! + t.hotWaterG!).toBe(t.waterG);
	});
});
