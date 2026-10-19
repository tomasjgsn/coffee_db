import { describe, expect, it } from 'vitest';
import { displayElapsedMs, eventLabels, liveShortcut } from './live-brew';

const key = (k: string, extra: Partial<Parameters<typeof liveShortcut>[0]> = {}) => ({
	key: k,
	repeat: false,
	metaKey: false,
	ctrlKey: false,
	altKey: false,
	...extra
});

describe('liveShortcut', () => {
	it('maps the brew keys to actions', () => {
		expect(liveShortcut(key(' '))).toBe('toggle-pour');
		expect(liveShortcut(key('s'))).toBe('swirl');
		expect(liveShortcut(key('t'))).toBe('stir');
		expect(liveShortcut(key('v'))).toBe('valve');
		expect(liveShortcut(key('p'))).toBe('press');
		expect(liveShortcut(key('d'))).toBe('drawdown');
		expect(liveShortcut(key('u'))).toBe('undo');
	});

	it('ignores auto-repeat from a held key', () => {
		expect(liveShortcut(key(' ', { repeat: true }))).toBeNull();
		expect(liveShortcut(key('s', { repeat: true }))).toBeNull();
	});

	it('ignores modifier chords such as Cmd+S', () => {
		expect(liveShortcut(key('s', { metaKey: true }))).toBeNull();
		expect(liveShortcut(key('d', { ctrlKey: true }))).toBeNull();
		expect(liveShortcut(key('u', { altKey: true }))).toBeNull();
	});

	it('leaves digits and other keys to the scale field', () => {
		expect(liveShortcut(key('5'))).toBeNull();
		expect(liveShortcut(key('.'))).toBeNull();
		expect(liveShortcut(key('Enter'))).toBeNull();
	});
});

describe('displayElapsedMs', () => {
	const startedAt = '2026-10-19T08:00:00.000Z';
	const start = Date.parse(startedAt);

	it('reads zero before the brew starts', () => {
		expect(displayElapsedMs(null, [], start + 5000)).toBe(0);
	});

	it('runs on the wall clock while brewing', () => {
		expect(displayElapsedMs(startedAt, [{ type: 'bloom_start', elapsedMs: 0 }], start + 42_000)).toBe(42_000);
	});

	it('freezes at the drawdown', () => {
		const events = [
			{ type: 'bloom_start', elapsedMs: 0 },
			{ type: 'drawdown_end', elapsedMs: 186_400 }
		];
		expect(displayElapsedMs(startedAt, events, start + 900_000)).toBe(186_400);
	});
});

describe('eventLabels', () => {
	it('closes the bloom as Bloom end and later pours as Pour end', () => {
		const labels = eventLabels([
			{ type: 'bloom_start', elapsedMs: 0 },
			{ type: 'pour_end', elapsedMs: 9_000 },
			{ type: 'swirl', elapsedMs: 12_000 },
			{ type: 'pour_start', elapsedMs: 45_000 },
			{ type: 'pour_end', elapsedMs: 60_000 },
			{ type: 'drawdown_end', elapsedMs: 180_000 }
		]);
		expect(labels).toEqual(['Bloom', 'Bloom end', 'Swirl', 'Pour', 'Pour end', 'Drawdown done']);
	});

	it('falls back to the raw type for unknown events', () => {
		expect(eventLabels([{ type: 'scale_tare', elapsedMs: 0 }])).toEqual(['scale_tare']);
	});
});
