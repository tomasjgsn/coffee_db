import { describe, expect, it } from 'vitest';
import { dotGlyphs, scoreForKey, tapDot } from './factor-score';

describe('tapDot', () => {
	it('sets the full value of an empty dot', () => {
		expect(tapDot(null, 3)).toBe(4);
	});

	it('cycles the same dot full, half, clear', () => {
		expect(tapDot(4, 3)).toBe(3.5);
		expect(tapDot(3.5, 3)).toBeNull();
		expect(tapDot(null, 3)).toBe(4);
	});

	it('moves straight to another dot', () => {
		expect(tapDot(4, 1)).toBe(2);
		expect(tapDot(2, 4)).toBe(5);
	});

	it('reaches a half point on the first dot', () => {
		expect(tapDot(1, 0)).toBe(0.5);
	});
});

describe('scoreForKey', () => {
	it('scores whole points with 1 to 5 and clears with 0', () => {
		expect(scoreForKey(null, '4')).toBe(4);
		expect(scoreForKey(2, '5')).toBe(5);
		expect(scoreForKey(3, '0')).toBeNull();
		expect(scoreForKey(3, 'Backspace')).toBeNull();
	});

	it('steps half points with the arrows, within 0.5 to 5', () => {
		expect(scoreForKey(null, 'ArrowRight')).toBe(0.5);
		expect(scoreForKey(3, 'ArrowUp')).toBe(3.5);
		expect(scoreForKey(5, 'ArrowRight')).toBe(5);
		expect(scoreForKey(3.5, 'ArrowLeft')).toBe(3);
		expect(scoreForKey(0.5, 'ArrowDown')).toBeNull();
		expect(scoreForKey(null, 'ArrowLeft')).toBeNull();
	});

	it('leaves other keys alone', () => {
		expect(scoreForKey(3, 'Tab')).toBeUndefined();
		expect(scoreForKey(3, '6')).toBeUndefined();
		expect(scoreForKey(3, ' ')).toBeUndefined();
	});
});

describe('dotGlyphs', () => {
	it('draws full, half and empty dots', () => {
		expect(dotGlyphs(4.5).join('')).toBe('●●●●◐');
		expect(dotGlyphs(3).join('')).toBe('●●●○○');
		expect(dotGlyphs(0.5).join('')).toBe('◐○○○○');
	});

	it('draws an unscored factor as five empty dots, never middots', () => {
		expect(dotGlyphs(null).join('')).toBe('○○○○○');
	});
});
