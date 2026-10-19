/**
 * Live brew logic kept out of the page so it can be tested: which key does
 * what, what the clock shows, and what each captured event is called.
 */

export type LiveAction = 'toggle-pour' | 'swirl' | 'stir' | 'valve' | 'press' | 'drawdown' | 'undo';

interface KeyLike {
	key: string;
	repeat: boolean;
	metaKey: boolean;
	ctrlKey: boolean;
	altKey: boolean;
}

interface EventLike {
	type: string;
	elapsedMs: number;
}

const KEYS: Record<string, LiveAction> = {
	' ': 'toggle-pour',
	s: 'swirl',
	t: 'stir',
	v: 'valve',
	p: 'press',
	d: 'drawdown',
	u: 'undo'
};

/**
 * The brew action for a keydown, or null. A held key's auto-repeat and any
 * modifier chord (Cmd+S, Ctrl+D) are never captures.
 */
export function liveShortcut(e: KeyLike): LiveAction | null {
	if (e.repeat || e.metaKey || e.ctrlKey || e.altKey) return null;
	return KEYS[e.key] ?? null;
}

/** Wall-clock elapsed time, held at the drawdown once it is called. */
export function displayElapsedMs(startedAt: string | null, events: EventLike[], now: number): number {
	if (!startedAt) return 0;
	const drawdown = events.find((e) => e.type === 'drawdown_end');
	if (drawdown) return drawdown.elapsedMs;
	return Math.max(0, now - Date.parse(startedAt));
}

const LABELS: Record<string, string> = {
	bloom_start: 'Bloom',
	pour_start: 'Pour',
	pour_end: 'Pour end',
	swirl: 'Swirl',
	stir: 'Stir',
	valve_open: 'Valve open',
	press_start: 'Press',
	press_end: 'Press end',
	drawdown_end: 'Drawdown done'
};

/** Display labels in order; the end of the bloom reads Bloom end. */
export function eventLabels(events: EventLike[]): string[] {
	let opener: string | null = null;
	return events.map((e) => {
		if (e.type === 'bloom_start' || e.type === 'pour_start') opener = e.type;
		if (e.type === 'pour_end') {
			const label = opener === 'bloom_start' ? 'Bloom end' : LABELS.pour_end;
			opener = null;
			return label;
		}
		return LABELS[e.type] ?? e.type;
	});
}
