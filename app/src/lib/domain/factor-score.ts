/**
 * Half-step 0.5 to 5 factor scores, entered without precision: one target
 * per dot, and keys for a focused factor.
 */

export type Score = number | null;

/** Tap dot `index` (0 to 4): another value sets that dot full; the same dot cycles full, half, clear. */
export function tapDot(current: Score, index: number): Score {
	const full = index + 1;
	if (current === full) return full - 0.5;
	if (current === full - 0.5) return null;
	return full;
}

/** The score after a key, or undefined when the key is not a scoring key. */
export function scoreForKey(current: Score, key: string): Score | undefined {
	if (/^[1-5]$/.test(key)) return Number(key);
	if (key === '0' || key === 'Backspace' || key === 'Delete') return null;
	if (key === 'ArrowRight' || key === 'ArrowUp') return Math.min(5, (current ?? 0) + 0.5);
	if (key === 'ArrowLeft' || key === 'ArrowDown') {
		if (current === null || current <= 0.5) return null;
		return current - 0.5;
	}
	return undefined;
}
