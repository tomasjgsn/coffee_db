import { describe, expect, it } from 'vitest';
import { dayNumber, monthHeading, pct, ratioLabel, score1, weekdayDay } from './format';

describe('display formatting', () => {
	it('formats ratios as 1:N', () => {
		expect(ratioLabel(16.7)).toBe('1:16.7');
		expect(ratioLabel(16)).toBe('1:16');
		expect(ratioLabel(null)).toBe('—');
	});

	it('formats percentages to one decimal', () => {
		expect(pct(21.2)).toBe('21.2%');
		expect(pct(20.31)).toBe('20.3%');
		expect(pct(null)).toBe('—');
	});

	it('formats scores to one decimal', () => {
		expect(score1(4)).toBe('4.0');
		expect(score1(4.167)).toBe('4.2');
		expect(score1(null)).toBe('—');
	});

	it('formats dates for menu headings and rows', () => {
		expect(monthHeading('2025-07-27')).toBe('July 2025');
		expect(dayNumber('2025-07-27')).toBe('27');
		expect(weekdayDay('2026-01-24')).toBe('Sat 24 Jan');
	});
});
