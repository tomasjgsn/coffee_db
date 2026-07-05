import { describe, expect, it } from 'vitest';
import {
	BOX_SLOPES,
	classifyRay,
	immersionEY,
	liquidRetainedRatio,
	ratioWindowForBox,
	raySlope,
	slopeForRatio
} from './rays';

describe('ray geometry on the control chart', () => {
	it('derives the box-reachable slope window from the frozen thresholds', () => {
		expect(BOX_SLOPES.min).toBeCloseTo(1.15 / 22, 6);
		expect(BOX_SLOPES.max).toBeCloseTo(1.35 / 18, 6);
	});

	it('computes a cup\'s ray slope as dose over brew mass', () => {
		// Cup Nº63: 16.2 g dose, 207.5 g beverage → TDS/EY ratio
		expect(raySlope(16.2, 207.5)).toBeCloseTo(0.0781, 4);
	});

	it('classifies rays against the ideal box', () => {
		expect(classifyRay(0.0781)).toBe('above');
		expect(classifyRay(0.065)).toBe('through');
		expect(classifyRay(0.048)).toBe('below');
		expect(classifyRay(BOX_SLOPES.max)).toBe('through');
		expect(classifyRay(BOX_SLOPES.min)).toBe('through');
	});

	it('converts a planned ratio + retention into a slope', () => {
		// Tomas's Switch: 1:15.4 at LRR 2.62 g/g → misses the box
		const switchSlope = slopeForRatio(15.4, 2.62);
		expect(switchSlope).toBeCloseTo(1 / 12.78, 4);
		expect(classifyRay(switchSlope!)).toBe('above');
		expect(slopeForRatio(2, 2.62)).toBeNull();
	});

	it('gives the reachable ratio window for a retention value', () => {
		const window = ratioWindowForBox(2.62);
		expect(window.min).toBeCloseTo(2.62 + 18 / 1.35, 2);
		expect(window.max).toBeCloseTo(2.62 + 22 / 1.15, 2);
		expect(window.min).toBeCloseTo(15.95, 1);
		expect(window.max).toBeCloseTo(21.75, 1);
	});

	it('measures liquid retained ratio from a finished cup', () => {
		expect(liquidRetainedRatio(16.2, 250, 207.5)).toBeCloseTo(2.62, 2);
		expect(liquidRetainedRatio(0, 250, 207.5)).toBeNull();
		expect(liquidRetainedRatio(16.2, null, 207.5)).toBeNull();
	});

	it('computes the immersion-mode EY reading (TDS × water / dose)', () => {
		expect(immersionEY(1.24, 250, 16.2)).toBeCloseTo(19.14, 2);
		expect(immersionEY(null, 250, 16.2)).toBeNull();
		expect(immersionEY(1.24, 250, 0)).toBeNull();
	});
});
