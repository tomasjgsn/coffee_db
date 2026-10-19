import { describe, expect, it } from 'vitest';
import { clock, countLabel, dayNumber, grams, monthHeading, parseClock, pct, ratioLabel, score1, weekdayDay, zoneLabel } from './format';

describe('display formatting', () => {
	it('formats ratios as 1:N', () => {
		expect(ratioLabel(16.7)).toBe('1:16.7');
		expect(ratioLabel(16)).toBe('1:16');
		expect(ratioLabel(null)).toBe('no ratio');
	});

	it('formats percentages to one decimal', () => {
		expect(pct(21.2)).toBe('21.2%');
		expect(pct(20.31)).toBe('20.3%');
		expect(pct(null)).toBe('no reading');
	});

	it('formats scores to one decimal', () => {
		expect(score1(4)).toBe('4.0');
		expect(score1(4.167)).toBe('4.2');
		expect(score1(null)).toBe('unscored');
	});

	it('says what is missing instead of printing a dash', () => {
		expect(grams(18)).toBe('18 g');
		expect(grams(null)).toBe('not logged');
		for (const text of [ratioLabel(null), pct(null), score1(null), grams(null)]) {
			expect(text).not.toMatch(/[\u2013\u2014]/);
		}
	});

	it('names zones in words, not as raw categories', () => {
		expect(zoneLabel('Ideal-Ideal')).toBe('ideal');
		expect(zoneLabel('Under-Ideal')).toBe('extraction under, strength ideal');
		expect(zoneLabel('Ideal-Strong')).toBe('extraction ideal, strength strong');
		expect(zoneLabel(null)).toBe('no reading');
	});

	it('counts with the right plural', () => {
		expect(countLabel(1, 'brew')).toBe('1 brew');
		expect(countLabel(3, 'brew')).toBe('3 brews');
		expect(countLabel(0, 'brew')).toBe('0 brews');
	});

	it('formats dates for menu headings and rows', () => {
		expect(monthHeading('2025-07-27')).toBe('July 2025');
		expect(dayNumber('2025-07-27')).toBe('27');
		expect(weekdayDay('2026-01-24')).toBe('Sat 24 Jan');
	});

	it('renders elapsed seconds as a clock', () => {
		expect(clock(0)).toBe('0:00');
		expect(clock(45)).toBe('0:45');
		expect(clock(182)).toBe('3:02');
		expect(clock(3675)).toBe('61:15');
	});

	it('parses typed times back to seconds', () => {
		expect(parseClock('3:02')).toBe(182);
		expect(parseClock('0:45')).toBe(45);
		expect(parseClock('45')).toBe(45);
		expect(parseClock("2'30")).toBe(150);
		expect(parseClock('')).toBeNull();
		expect(parseClock('nonsense')).toBeNull();
		expect(parseClock('1:75')).toBeNull();
	});
});
