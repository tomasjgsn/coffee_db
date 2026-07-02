import { describe, expect, it } from 'vitest';
import {
	pyRound,
	brewRatio,
	extractionYield,
	coffeeGramsPerLiter,
	strengthCategory,
	extractionCategory,
	brewingZone,
	brewScore,
	overallRating,
	daysSinceRoast,
	parseFlexibleDate
} from './calculations';

describe('pyRound — CPython round() semantics (half-to-even on decimal value)', () => {
	it('rounds exact halves to even', () => {
		expect(pyRound(2.5, 0)).toBe(2);
		expect(pyRound(3.5, 0)).toBe(4);
		expect(pyRound(18.25, 1)).toBe(18.2);
		expect(pyRound(18.75, 1)).toBe(18.8);
		expect(pyRound(0.125, 2)).toBe(0.12);
	});

	it('rounds by the true decimal value of the double, not naive scaling', () => {
		expect(pyRound(2.675, 2)).toBe(2.67);
		expect(pyRound(6.55, 1)).toBe(6.5);
		expect(pyRound(18.35, 1)).toBe(18.4);
	});

	it('handles plain cases and negatives', () => {
		expect(pyRound(16.666666, 1)).toBe(16.7);
		expect(pyRound(20.3089, 2)).toBe(20.31);
		expect(pyRound(-18.25, 1)).toBe(-18.2);
		expect(pyRound(-0.4, 1)).toBe(-0.4);
	});
});

describe('brewRatio — water/dose rounded to 1 dp', () => {
	it('matches process_entry_data._calculate_brew_ratio', () => {
		expect(brewRatio(300, 18)).toBe(16.7);
		expect(brewRatio(250, 15.5)).toBe(16.1);
		expect(brewRatio(300, 16)).toBe(18.8);
	});
	it('throws on zero dose like the Python ZeroDivisionError path', () => {
		expect(() => brewRatio(300, 0)).toThrow();
	});
});

describe('extractionYield — mass × TDS / dose rounded to 2 dp', () => {
	it('matches the UC Davis formula used in Python', () => {
		expect(extractionYield(264.9, 1.38, 18)).toBe(20.31);
		expect(extractionYield(280, 1.25, 17)).toBe(20.59);
		expect(extractionYield(250, 1.2, 15)).toBe(20);
	});
});

describe('coffeeGramsPerLiter — dose/water × 1000 rounded to 1 dp', () => {
	it('matches Python', () => {
		expect(coffeeGramsPerLiter(18, 300)).toBe(60);
		expect(coffeeGramsPerLiter(15.5, 250)).toBe(62);
		expect(coffeeGramsPerLiter(18, 280)).toBe(64.3);
	});
});

describe('strength/extraction categories — inclusive ideal bounds', () => {
	it('classifies strength: weak < 1.15 ≤ ideal ≤ 1.35 < strong', () => {
		expect(strengthCategory(1.14)).toBe('Weak');
		expect(strengthCategory(1.15)).toBe('Ideal');
		expect(strengthCategory(1.35)).toBe('Ideal');
		expect(strengthCategory(1.36)).toBe('Strong');
	});
	it('classifies extraction: under < 18 ≤ ideal ≤ 22 < over', () => {
		expect(extractionCategory(17.99)).toBe('Under');
		expect(extractionCategory(18)).toBe('Ideal');
		expect(extractionCategory(22)).toBe('Ideal');
		expect(extractionCategory(22.01)).toBe('Over');
	});
	it('builds the zone as extraction-strength', () => {
		expect(brewingZone(1.2, 20)).toBe('Ideal-Ideal');
		expect(brewingZone(1.1, 17)).toBe('Under-Weak');
		expect(brewingZone(1.4, 23)).toBe('Over-Strong');
	});
});

describe('brewScore — 0.6×rating + 0.4×zone bonus, rounded to 1 dp', () => {
	it('applies bonuses 10 / 7 / 4', () => {
		expect(brewScore(4, 'Ideal-Ideal')).toBe(6.4);
		expect(brewScore(3.5, 'Under-Ideal')).toBe(4.9);
		expect(brewScore(3.5, 'Ideal-Weak')).toBe(4.9);
		expect(brewScore(3.5, 'Under-Weak')).toBe(3.7);
	});
	it('returns null without a rating and defaults unknown zones to 4', () => {
		expect(brewScore(null, 'Ideal-Ideal')).toBeNull();
		expect(brewScore(undefined, 'Ideal-Ideal')).toBeNull();
		expect(brewScore(3, 'Nonsense-Zone')).toBe(3.4);
	});
});

describe('overallRating — mean of three factors, rounded to 3 dp', () => {
	it('matches ThreeFactorScoringService.calculate_overall_score', () => {
		expect(overallRating(4, 3.5, 4.5)).toBe(4);
		expect(overallRating(4, 3, 3.5)).toBe(3.5);
		expect(overallRating(4.5, 3.5, 3.5)).toBe(3.833);
		expect(overallRating(0.5, 0.5, 1)).toBe(0.667);
	});
	it('returns null when any factor is missing', () => {
		expect(overallRating(4, null, 4)).toBeNull();
	});
});

describe('daysSinceRoast — brew date minus purchase date', () => {
	it('computes whole days from ISO dates', () => {
		expect(daysSinceRoast('2025-08-10', '2025-07-28')).toBe(13);
		expect(daysSinceRoast('2025-08-10', '2025-08-10')).toBe(0);
	});
	it('returns null for negative spans or missing dates', () => {
		expect(daysSinceRoast('2025-07-01', '2025-07-28')).toBeNull();
		expect(daysSinceRoast(null, '2025-07-28')).toBeNull();
		expect(daysSinceRoast('2025-07-28', null)).toBeNull();
	});
});

describe('parseFlexibleDate — ISO standard plus legacy D/M/YY', () => {
	it('parses ISO dates and datetimes to YYYY-MM-DD', () => {
		expect(parseFlexibleDate('2025-08-10')).toBe('2025-08-10');
		expect(parseFlexibleDate('2025-08-10 07:41:00')).toBe('2025-08-10');
	});
	it('parses legacy D/M/YY with 2000s pivot at 30', () => {
		expect(parseFlexibleDate('28/7/25')).toBe('2025-07-28');
		expect(parseFlexibleDate('01/12/24')).toBe('2024-12-01');
	});
	it('returns null for blanks and rejects garbage', () => {
		expect(parseFlexibleDate('')).toBeNull();
		expect(parseFlexibleDate('  ')).toBeNull();
		expect(() => parseFlexibleDate('not a date')).toThrow();
	});
});
